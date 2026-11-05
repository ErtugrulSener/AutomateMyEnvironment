import os
from unittest.mock import Mock, call

import pytest

from scripts.managers.configuration_update_manager import ConfigurationUpdateManager
from scripts.managers.software_manager import SoftwareManager
from scripts.managers.software_update_manager import SoftwareUpdateManager
from scripts.parsers.config_parser import ConfigParser


UPDATERS = [
    (SoftwareUpdateManager, "SoftwareUpdater", "software_update_manager.py"),
    (ConfigurationUpdateManager, "ConfigurationUpdater", "configuration_update_manager.py"),
]


@pytest.mark.parametrize(("updater", "service", "script"), UPDATERS)
def test_service_registration_uses_global_scoop_python_314(
        tmp_path, monkeypatch, fresh, commands, updater, service, script):
    monkeypatch.chdir(tmp_path)
    scoop_root = tmp_path / "Global Scoop"
    monkeypatch.setenv("SCOOP_GLOBAL", str(scoop_root))
    monkeypatch.setenv("ALIAS", "test-machine")
    monkeypatch.setattr(os, "getlogin", lambda: "test-user")
    for name in ("http_proxy", "https_proxy"):
        monkeypatch.delenv(name, raising=False)
    fresh(SoftwareManager)
    commands.reset_mock()

    fresh(updater).register_service()

    python = scoop_root / "apps" / "python314" / "current" / "python.exe"
    updater_script = tmp_path / "scripts" / "managers" / script
    assert commands.call_args_list[0] == call(f'nssm install {service} "{python}" "{updater_script}"')
    assert commands.call_args_list[1] == call(
        f'nssm set {service} AppEnvironmentExtra HOME="{tmp_path}" USER="test-user" ALIAS="test-machine"'
    )
    assert (tmp_path / "logs").is_dir()


@pytest.mark.parametrize(("updater", "service"), [(manager, name) for manager, name, _ in UPDATERS])
@pytest.mark.parametrize(("status", "should_register", "should_start"), [
    ("SERVICE_RUNNING", False, False),
    ("SERVICE_START_PENDING", False, False),
    ("SERVICE_STOPPED", False, True),
    ("SERVICE_STOPPED", True, True),
])
def test_service_lifecycle_registers_or_starts_only_when_needed(
        monkeypatch, fresh, commands, updater, service, status, should_register, should_start):
    manager = fresh(updater)
    status_output = ("\0".join(status) + "\0\n", 0)
    initial_output = ("OpenService(): The specified service does not exist.\n", 3) if should_register else status_output
    commands.side_effect = [initial_output, status_output, ""]
    register = Mock()
    monkeypatch.setattr(manager, "register_service", register)

    manager.check_for_services()

    status_command = call(f"nssm status {service}")
    expected_calls = [status_command, status_command]
    if should_start:
        expected_calls.append(call(f"nssm start {service}"))
    assert commands.call_args_list == expected_calls
    assert register.call_count == int(should_register)


def test_software_manager_reads_scoop_inventory_and_install_arguments(monkeypatch, fresh, commands):
    commands.return_value = (
        "Installed apps:\n\nName Version Source Updated\n---- ------- ------ -------\n"
        "git 2.0 main 2026-01-01\ncmder 1.2 extras 2026-01-01\n\n"
    )
    config = fresh(ConfigParser)
    config.read_dict({"SOFTWARE_LIST": {"git": "--install-context --keep-all-old-versions"}})
    monkeypatch.setenv("SCOOP_GLOBAL", r"C:\Test Scoop")

    manager = fresh(SoftwareManager)

    assert manager.is_installed("git")
    assert not manager.is_installed("missing")
    args = manager.get_install_arguments("git")
    assert args.install_context and args.keep_all_old_versions
    assert not manager.exists_in_softwarelist("cmder")
    assert manager.get_path("GIT", "git.exe") == r"C:\Test Scoop\apps\git\current\git.exe"
    commands.assert_called_once_with("scoop list")


def test_updater_replaces_stale_outdated_list_and_skips_failed_installs(monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP", r"C:\Test Scoop")
    commands.return_value = (
        "Name Installed Version Latest Version Missing Dependencies Info\n"
        "------------------------------------------------------------\n"
        "git 2.50.0 2.51.0\n"
        "failed-app 1.0 2.0 Install failed\n"
    )
    manager = fresh(SoftwareUpdateManager)
    manager.outdated_software = [("stale", "1", "2")]

    manager.refresh_outdated_software()

    assert manager.outdated_software == [("git", "2.50.0", "2.51.0")]
    commands.assert_called_once_with(r"C:\Test Scoop\shims\scoop.cmd status --global")


@pytest.mark.parametrize(("output", "sends_notification", "keeps_old"), [
    ("ERROR git is still running", False, False),
    ("Updated git", True, False),
    ("Updated git", True, True),
])
def test_updater_only_notifies_and_cleans_after_success(
        monkeypatch, fresh, commands, output, sends_notification, keeps_old):
    monkeypatch.setenv("SCOOP", r"C:\Test Scoop")
    commands.return_value = output
    manager = fresh(SoftwareUpdateManager)
    notify = Mock()
    cleanup = Mock()
    monkeypatch.setattr(manager, "send_push_message", notify)
    monkeypatch.setattr(manager, "cleanup", cleanup)
    monkeypatch.setattr(manager, "keep_old_version_of", lambda software: keeps_old)

    manager.update("git", "2.50.0", "2.51.0")

    commands.assert_called_once_with(r"C:\Test Scoop\shims\scoop.cmd update --global git")
    assert notify.call_args_list == ([call("git", "2.50.0", "2.51.0")] if sends_notification else [])
    assert cleanup.call_args_list == ([call("git")] if sends_notification and not keeps_old else [])
