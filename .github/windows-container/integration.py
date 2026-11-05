import base64
import configparser
import json
import os
import runpy
import subprocess
import sys
import threading
import time
import zipfile
from contextlib import ExitStack
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch


if os.environ.get("AUTOMATION_CONTAINER_INTEGRATION") != "1" or Path.cwd() != Path("C:/Automation"):
    raise SystemExit("This integration test requires the disposable Automation container")

sys.path.insert(0, str(Path.cwd()))

from scripts.checkers.system_checker import SystemChecker
from scripts.configurators.configurator import Configurator
from scripts.configurators.software.notepadplusplus_configurator import NotepadPlusPlusConfigurator
from scripts.managers.aes_manager import AESManager
from scripts.managers.configuration_update_manager import ConfigurationUpdateManager
from scripts.managers.database_manager import Constant, DatabaseManager
from scripts.managers.push_notifier_manager import PushNotifierManager
from scripts.managers.software_manager import SoftwareManager
from scripts.managers.software_update_manager import SoftwareUpdateManager


SKIPPED = {
    "WindowsDefenderConfigurator": "Defender is absent on Server Core",
    "WindowsDesktopConfigurator": "No interactive desktop",
    "WindowsEnergySavingPlanConfigurator": "Container has no independent power plan",
    "WindowsFileAssociationConfigurator": "No Explorer user session",
    "WindowsDefaultBrowserConfigurator": "No desktop browser installation",
    "WindowsTaskbarConfigurator": "No Explorer taskbar",
    "WindowsScreenResolutionConfigurator": "No interactive display",
    "WindowsSSHCredentialsConfigurator": "SSH agent and real SSH credentials are excluded",
}
report = {
    "passed": [],
    "skipped": {},
    "fixtures": [
        "Synthetic git-crypt key and AES password",
        "Local HTTP release endpoint and plugin archive",
        "Application configuration directories and license placeholders",
        "Push messages recorded locally",
        "Updater services run a ready-marker worker instead of update loops",
        "Internet HEAD request routed to the local HTTP fixture",
        "Defender precondition omitted because Defender is absent",
    ],
}
services = []


def execute(*arguments):
    try:
        output = subprocess.check_output(arguments, text=True, encoding="cp850", stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        print(error.output, flush=True)
        raise
    return output.replace("\x00", "").strip()


def record(name):
    report["passed"].append(name)
    print(f"INTEGRATION PASS {name}", flush=True)


def start_fixture_service(name):
    marker = Path("logs", name + ".ready")
    execute("nssm", "set", name, "AppParameters", f'"C:\\ci\\fixture_worker.py" "{name}"')
    execute("nssm", "start", name)
    for attempt in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.read_text(encoding="ascii") == "ready", name
    assert execute("nssm", "status", name) == "SERVICE_RUNNING", name


def exercise_updater(manager_type, name):
    manager = manager_type.instance()
    manager.register_service()
    services.append(name)
    executable = execute("nssm", "get", name, "Application")
    assert Path(executable) == Path(sys.executable), executable
    start_fixture_service(name)
    assert manager.service_is_running()
    record(name + " registration and real service startup")


def prepare_files(endpoint):
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read_dict({
        "SOFTWARE_LIST": {"nano": "", "wget": ""},
        "GIT": {"automation.container-fixture": "enabled"},
        "INTELLIJ": {"settings-repository": "C:/Automation/fixture-settings"},
        "WINDOWS-SERVICES": {"AutomationFixtureService": "--start-mode Manual --action start"},
    })
    with open("config.ini", "w") as output:
        config.write(output)
    settings = Path("fixture-settings")
    settings.mkdir()
    (settings / "settings.txt").write_text("synthetic IDE settings", encoding="ascii")
    execute("git", "init", "--quiet", str(settings))
    execute("git", "-C", str(settings), "add", ".")
    execute("git", "-C", str(settings), "-c", "user.name=ContainerTest", "-c",
            "user.email=container@example.invalid", "commit", "--quiet", "-m", "Synthetic IDE settings")
    Path("alias").write_text("container-fixture", encoding="ascii")
    for relative in (
        "apps/cmder/current/vendor/conemu-maximus5",
        "apps/notepadplusplus/current/plugins",
        "apps/winscp/current",
        "apps/idea/current/IDE",
        "persist/brave/User Data",
    ):
        Path("C:/Software", relative).mkdir(parents=True, exist_ok=True)
    Path("C:/Software/apps/winscp/current/winscp.ini").write_text("[Unrelated]\nKeepMe=yes\n", encoding="ascii")
    Path("C:/Software/apps/idea/current/IDE/product-info.json").write_text(
        json.dumps({"dataDirectoryName": "ContainerFixtureIdea"}), encoding="ascii"
    )
    licenses = Path("secrets/licenses/idea")
    licenses.mkdir(parents=True)
    for name in ("plugin_PCWMP.license", "idea.key"):
        (licenses / name).write_text("synthetic license placeholder", encoding="ascii")
    key = Path("secrets/keys/private_openssh")
    key.parent.mkdir(parents=True)
    key.write_text("synthetic private-key fixture", encoding="ascii")
    Path(".gitattributes").write_text("secrets/** filter=git-crypt diff=git-crypt\n", encoding="ascii")
    execute("git-crypt", "init")
    execute("git-crypt", "export-key", "fixture.key")
    execute("git", "add", "config.ini", ".gitattributes", "secrets")
    execute("git", "-c", "user.name=ContainerTest", "-c", "user.email=container@example.invalid",
            "commit", "--quiet", "-m", "Synthetic integration fixtures")
    execute("git-crypt", "lock")
    assert key.read_bytes().startswith(b"\x00GITCRYPT")
    exported_key = Path("fixture.key")
    encrypted = AESManager.instance().encrypt(base64.b64encode(exported_key.read_bytes()).decode(), "0123456789abcdef")
    Path("secret").write_bytes(encrypted)
    exported_key.unlink()
    web = Path("fixture-web")
    with zipfile.ZipFile(web / "ComparePlus_fixture_x64.zip", "w") as archive:
        archive.writestr("ComparePlus.dll", b"synthetic plugin fixture")
    (web / "latest").write_text(json.dumps({
        "assets": [{"browser_download_url": endpoint + "/ComparePlus_fixture_x64.zip"}]
    }), encoding="ascii")


def main():
    os.environ["PATH"] = str(Path("external/executables/nssm").resolve()) + os.pathsep + os.environ["PATH"]
    for fixture in report["fixtures"]:
        print(f"INTEGRATION FIXTURE {fixture}", flush=True)
    Path("logs").mkdir(exist_ok=True)
    web = Path("fixture-web")
    web.mkdir()
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(web.resolve())))
    endpoint = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    prepare_files(endpoint)
    original_configure = Configurator._decorated.configure

    def configure(dispatcher, configurator_type):
        name = configurator_type._decorated.__name__
        if name in SKIPPED:
            report["skipped"][name] = SKIPPED[name]
            print(f"INTEGRATION SKIP {name} - {SKIPPED[name]}", flush=True)
            return
        original_configure(dispatcher, configurator_type)
        configurator_type._instance = None
        configurator = configurator_type.instance()
        if name == "WindowsServicesConfigurator":
            for attempt in range(50):
                if configurator.is_configured_already():
                    break
                time.sleep(0.1)
        assert configurator.is_configured_already(), name
        record(name)

    def software_updater():
        exercise_updater(SoftwareUpdateManager, "SoftwareUpdater")
        execute("nssm", "install", "AutomationFixtureService", sys.executable, "C:\\ci\\fixture_worker.py",
                "AutomationFixtureService")
        services.append("AutomationFixtureService")

    notifications = Mock()
    notifications.send_text.side_effect = lambda text: print(f"INTEGRATION NOTIFICATION {text}", flush=True)
    import requests
    from scripts.checkers import secrets_checker

    original_head = requests.head
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(SystemChecker._decorated, "check_for_tamper_protection", lambda self: None))
            stack.enter_context(patch.object(secrets_checker.pwinput, "pwinput", return_value="0123456789abcdef"))
            stack.enter_context(patch.object(PushNotifierManager, "instance", return_value=notifications))
            stack.enter_context(patch.object(requests, "head", lambda url, **kwargs: original_head(endpoint, **kwargs)))
            stack.enter_context(patch.object(Configurator._decorated, "configure", configure))
            stack.enter_context(patch.object(SoftwareUpdateManager.instance(), "start", software_updater))
            stack.enter_context(patch.object(ConfigurationUpdateManager.instance(), "start",
                                            lambda: exercise_updater(ConfigurationUpdateManager, "ConfigurationUpdater")))
            stack.enter_context(patch.object(NotepadPlusPlusConfigurator._decorated, "PLUGIN_LIST", [
                ["ComparePlus", "ComparePlus_.*_x64.zip", endpoint + "/latest"],
            ]))
            sys.argv = ["install.py"]
            runpy.run_path("install.py", run_name="__main__")
        assert notifications.send_text.call_count == 4
        assert notifications.send_text.call_args.args[0].startswith("4/4")
        assert Path("secrets/keys/private_openssh").read_text() == "synthetic private-key fixture"
        assert Path("secret_decrypted").read_bytes().startswith(b"\x00GITCRYPTKEY")
        assert Path("C:/Software/apps/notepadplusplus/current/plugins/ComparePlus/ComparePlus.dll").read_bytes() == (
            b"synthetic plugin fixture"
        )
        assert SoftwareManager.instance().is_installed("nano")
        assert Path("logs/AutomationFixtureService.ready").read_text(encoding="ascii") == "ready"
        assert execute("git", "config", "--global", "--get", "automation.container-fixture") == "enabled"
        database = DatabaseManager.instance()
        database.set(Constant.POWER_SAVINGS_PLAN_GUID, "container's fixture")
        database.connection.close()
        DatabaseManager._instance = None
        database = DatabaseManager.instance()
        assert database.get(Constant.POWER_SAVINGS_PLAN_GUID) == "container's fixture"
        database.connection.close()
        record("SQLite value persisted and reloaded")
        record("Installer reached its final 4/4 notification with fixture boundaries")
    finally:
        server.shutdown()
        server.server_close()
        for name in reversed(services):
            status = execute("nssm", "status", name)
            if status == "SERVICE_RUNNING":
                execute("nssm", "stop", name)
            execute("nssm", "remove", name, "confirm")


try:
    main()
except BaseException as error:
    report["failure"] = f"{type(error).__name__}: {error}"
    raise
finally:
    Path("container-integration.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
