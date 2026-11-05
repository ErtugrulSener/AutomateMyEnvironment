import os
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.singleton import Singleton


ROOT = Path(__file__).resolve().parents[1]
MANAGERS = ROOT / "scripts" / "managers"


@pytest.fixture
def components(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setattr(sys, "argv", ["automation"])
    calls = Mock()
    instances = {
        "Logger": calls.logger,
        "Parser": calls.parser,
        "Checker": calls.checker,
        "Configurator": calls.configurator,
        "PushNotifierManager": calls.notifications,
        "SoftwareManager": calls.software,
        "SoftwareUpdateManager": calls.software_updater,
        "ConfigurationUpdateManager": calls.configuration_updater,
    }

    def get_instance(singleton):
        return instances[singleton._decorated.__name__]

    monkeypatch.setattr(Singleton, "instance", get_instance)
    return calls


def run_installer():
    # The services configurator constructs its WMI client at import time.
    with patch("wmi.WMI"):
        runpy.run_path(str(ROOT / "install.py"), run_name="__main__")


def test_installer_orders_preflight_installation_and_configuration(components):
    run_installer()

    methods = [entry[0] for entry in components.mock_calls]
    assert methods[:10] == [
        "logger.install", "parser.parse", "parser.parse", "checker.check", "checker.check", "checker.check",
        "notifications.send_text", "software.start", "software_updater.start", "configuration_updater.start",
    ]
    checks = [entry.args[0]._decorated.__name__ for entry in components.checker.check.call_args_list]
    assert checks == ["SystemChecker", "SecretsChecker", "AliasChecker"]
    parsers = [entry.args[0]._decorated.__name__ for entry in components.parser.parse.call_args_list]
    assert parsers == ["ArgumentParser", "ConfigParser"]

    configurations = [entry.args[0]._decorated.__name__ for entry in components.configurator.configure.call_args_list]
    assert configurations[0] == "WindowsUACConfigurator"
    assert configurations.index("WindowsScreenResolutionConfigurator") < configurations.index("BraveConfigurator")
    assert configurations[-1] == "PyCharmConfigurator"
    assert [entry.args[0][:3] for entry in components.notifications.send_text.call_args_list] == [
        "1/4", "2/4", "3/4", "4/4",
    ]
    assert methods[-1] == "notifications.send_text"


def test_installer_aborts_before_mutations_on_preflight_failure(components):
    components.checker.check.side_effect = SystemExit(3)

    with pytest.raises(SystemExit) as failure:
        run_installer()

    assert failure.value.code == 3
    components.checker.check.assert_called_once()
    components.software.start.assert_not_called()
    components.software_updater.start.assert_not_called()
    components.configuration_updater.start.assert_not_called()
    components.configurator.configure.assert_not_called()
    components.notifications.send_text.assert_not_called()


def test_installer_does_not_report_success_when_installation_fails(components):
    components.software.start.side_effect = subprocess.CalledProcessError(1, "scoop install")

    with pytest.raises(subprocess.CalledProcessError):
        run_installer()

    components.notifications.send_text.assert_called_once()
    assert components.notifications.send_text.call_args.args[0].startswith("1/4")
    components.software_updater.start.assert_not_called()
    components.configuration_updater.start.assert_not_called()
    components.configurator.configure.assert_not_called()


@pytest.fixture
def service_workspace(tmp_path, monkeypatch):
    home = tmp_path / "Automation folder"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.mark.parametrize(("connection", "expected_sleeps"), [
    ([True], [3600]),
    ([False, False, True], [10, 3600]),
])
def test_software_service_waits_for_connection_and_then_runs_one_update_cycle(
        monkeypatch, components, service_workspace, connection, expected_sleeps):
    updater = components.software_updater
    updater.check_for_connectivity.side_effect = connection

    def sleep(seconds):
        if seconds == 3600:
            raise KeyboardInterrupt

    components.sleep.side_effect = sleep
    monkeypatch.setattr(time, "sleep", components.sleep)

    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(MANAGERS / "software_update_manager.py"), run_name="__main__")

    assert stopped.value.code == 0
    assert Path.cwd() == service_workspace
    components.logger.install.assert_called_once_with(r"logs\software_updater_service.log")
    assert [entry.args[0] for entry in components.sleep.call_args_list] == expected_sleeps
    updater.check_for_scoop_updates.assert_called_once_with()
    updater.check_for_updates.assert_called_once_with()
    methods = [entry[0] for entry in components.mock_calls]
    assert methods.index("software_updater.check_for_scoop_updates") < methods.index("software_updater.check_for_updates")


def test_configuration_service_runs_then_exits_cleanly_on_interrupt(monkeypatch, components, service_workspace):
    components.sleep.side_effect = KeyboardInterrupt
    monkeypatch.setattr(time, "sleep", components.sleep)

    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(MANAGERS / "configuration_update_manager.py"), run_name="__main__")

    assert stopped.value.code == 0
    assert Path.cwd() == service_workspace
    components.logger.install.assert_called_once_with(r"logs\configuration_updater_service.log")
    components.configuration_updater.start.assert_called_once_with()
    components.sleep.assert_called_once_with(30)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Fallback resolves the checkout from the Scoop cwd")
@pytest.mark.parametrize("script", ["software_update_manager.py", "configuration_update_manager.py"])
def test_service_without_home_locates_repository_from_its_script(tmp_path, monkeypatch, components, script):
    source = tmp_path / "checkout" / "scripts" / "managers" / script
    source.parent.mkdir(parents=True)
    shutil.copyfile(MANAGERS / script, source)
    working_directory = tmp_path / "scoop" / "apps" / "python314" / "current"
    working_directory.mkdir(parents=True)
    monkeypatch.chdir(working_directory)
    monkeypatch.delenv("HOME", raising=False)
    seen_working_directory = Mock(side_effect=KeyboardInterrupt)
    components.logger.install.side_effect = lambda log_path: seen_working_directory(os.getcwd())

    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(source), run_name="__main__")

    assert stopped.value.code == 0
    seen_working_directory.assert_called_once_with(str(tmp_path / "checkout"))
