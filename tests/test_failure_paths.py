import os
import subprocess
import sys
from unittest.mock import MagicMock, Mock, call

import pytest
import requests

from scripts.commands.command_executor import CommandExecutor
from scripts.configurators.software.git_configurator import GitConfigurator
from scripts.configurators.windows.windows_energy_saving_plan_configurator import WindowsEnergySavingPlanConfigurator
from scripts.configurators.windows.windows_ssh_credentials_configurator import WindowsSSHCredentialsConfigurator
from scripts.configurators.windows.windows_taskbar_configurator import WindowsTaskbarConfigurator
from scripts.managers import network_manager
from scripts.managers.database_manager import Constant, DatabaseManager
from scripts.managers.explorer_manager import ExplorerManager
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.managers.software_update_manager import SoftwareUpdateManager
from scripts.parsers.argument_parser import ArgumentParser


SCOOP_LIST_OUTPUT = (
    "Installed apps:\n\nName Version Source Updated Info\n---- ------- ------ ------- ----\n"
    "git 2.0 main 2026-01-01 18:46:08 Global install\n"
    "other 1.0 main 2026-01-01 18:46:08 Global install\n\n"
)


@pytest.mark.xfail(strict=True, raises=KeyError, reason="HTTPS proxy handling requires an HTTP proxy")
def test_https_only_proxy_is_applied_without_changing_http_proxy(monkeypatch, fresh):
    proxy = "http://https-proxy.example.test:8080"
    existing_http_proxy = "http://existing-proxy.example.test:8080"
    monkeypatch.setattr(sys, "argv", ["install.py", "--https-proxy", proxy])
    monkeypatch.setenv("HTTP_PROXY", existing_http_proxy)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)

    fresh(ArgumentParser).parse()

    assert os.environ["HTTPS_PROXY"] == proxy
    assert os.environ["HTTP_PROXY"] == existing_http_proxy


@pytest.mark.parametrize("error", [
    requests.ConnectTimeout,
    pytest.param(requests.ReadTimeout, marks=pytest.mark.xfail(
        strict=True, raises=requests.ReadTimeout, reason="Connectivity check does not handle read timeouts"
    )),
])
def test_network_check_reports_unavailable_after_timeout(monkeypatch, fresh, error):
    head = Mock(side_effect=error)
    monkeypatch.setattr(network_manager.requests, "head", head)

    assert fresh(network_manager.NetworkManager).has_internet_connection() is False
    head.assert_called_once_with("https://8.8.8.8", timeout=5)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Executor appends to the caller's list")
def test_command_executor_does_not_mutate_callers_accepted_codes():
    accepted_codes = [3]
    executor = CommandExecutor(expected_return_codes=accepted_codes)

    assert executor.expected_return_codes == [3, 0]
    assert accepted_codes == [3]


@pytest.mark.xfail(strict=True, raises=AttributeError, reason="Executor returns None for empty stdout")
def test_file_association_manager_accepts_successful_command_with_empty_stdout(monkeypatch, fresh):
    popen = MagicMock()
    process = popen.return_value.__enter__.return_value
    process.stdout = iter(())
    process.returncode = 0
    monkeypatch.setattr(subprocess, "Popen", popen)

    associations = fresh(FileAssociationManager)

    assert associations.get(".txt") is None
    process.wait.assert_called_once_with()


@pytest.mark.parametrize("output", [
    pytest.param("core.autocrlf\ncore.ignorecase=true\n", id="implicit", marks=pytest.mark.xfail(
        strict=True, raises=ValueError, reason="Git prints implicit booleans without an equals sign"
    )),
    pytest.param("core.autocrlf=true\ncore.ignorecase=true\n", id="explicit"),
])
def test_git_config_reads_explicit_and_implicit_values(fresh, commands, output):
    commands.return_value = output

    config = fresh(GitConfigurator)

    assert config.is_config_set("core.autocrlf")
    assert config.is_config_set("core.ignorecase")


ssh_comment_bug = pytest.mark.xfail(strict=True, raises=ValueError, reason="SSH parser requires exactly three words")


@pytest.mark.parametrize("comment", [
    pytest.param("single-word", id="single-word"),
    pytest.param("comment with spaces", id="multiple-words", marks=ssh_comment_bug),
    pytest.param("", id="empty-comment", marks=ssh_comment_bug),
])
def test_ssh_agent_reads_keys_with_optional_free_text_comments(fresh, commands, comment):
    key = "fixture-key"
    commands.return_value = f"ssh-ed25519 {key} {comment}\n"

    configurator = fresh(WindowsSSHCredentialsConfigurator)

    assert configurator.ssh_keys == [key]
    commands.assert_called_once_with("ssh-add -L")


@pytest.mark.xfail(strict=True, raises=FileNotFoundError, reason="Taskbar assumes the pinned-shortcuts directory exists")
def test_taskbar_can_configure_a_profile_without_a_pinned_shortcuts_directory(tmp_path, monkeypatch, fresh):
    missing_directory = tmp_path / "TaskBar"
    registry = Mock()
    registry.check_all.return_value = False
    explorer = Mock()
    monkeypatch.setattr(RegistryManager, "instance", lambda: registry)
    monkeypatch.setattr(ExplorerManager, "instance", lambda: explorer)
    configurator = fresh(WindowsTaskbarConfigurator)
    monkeypatch.setattr(configurator, "USER_PINNED_QUICK_LAUNCH_PATH", missing_directory)

    configurator.configure()

    registry.set_all.assert_called_once_with(configurator.EXPECTED_REGISTRY_ENTRIES)
    registry.delete_tree.assert_called_once_with(RegistryPath.WINDOWS_EXPLORER_TASKBAND)
    explorer.restart.assert_called_once_with()
    assert not missing_directory.exists()


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Power plan import runs even when the built-in plan exists")
def test_power_plan_keeps_existing_builtin_plan_without_importing_another(monkeypatch, fresh, commands):
    plan_type = WindowsEnergySavingPlanConfigurator._decorated
    guid = plan_type.TARGET_GUID

    def execute(command):
        if command == "powercfg /l":
            return f"Power plans\n-----------\n\nPower Scheme GUID: {guid} (High performance) *\n"
        if command.startswith("powercfg /q "):
            return ""
        if command.startswith("powercfg /import "):
            return "GUID: 12345678-abcd-1234-abcd-123456789abc"
        raise AssertionError(command)

    commands.side_effect = execute
    database = Mock()
    monkeypatch.setattr(DatabaseManager, "instance", lambda: database)
    configurator = fresh(WindowsEnergySavingPlanConfigurator)

    assert configurator.TARGET_GUID == guid
    assert configurator.power_configurations == {guid: True}
    database.get.assert_not_called()
    database.set.assert_not_called()
    assert not any(entry.args[0].startswith("powercfg /import ") for entry in commands.call_args_list)


def test_power_plan_imports_and_records_missing_plan(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.chdir(tmp_path)
    guid = "12345678-abcd-1234-abcd-123456789abc"
    database = Mock()
    database.get.return_value = None
    monkeypatch.setattr(DatabaseManager, "instance", lambda: database)
    commands.side_effect = ["Power plans\n-----------\n\n", f"Imported power plan. GUID: {guid}\n", "", "", "", ""]

    configurator = fresh(WindowsEnergySavingPlanConfigurator)

    assert configurator.TARGET_GUID == guid
    assert configurator.power_configurations == {guid: False}
    database.get.assert_called_once_with(Constant.POWER_SAVINGS_PLAN_GUID)
    database.set.assert_called_once_with(Constant.POWER_SAVINGS_PLAN_GUID, guid)


@pytest.mark.parametrize("reinstall", [False, True])
def test_software_installer_only_reinstalls_when_requested(monkeypatch, fresh, commands, reinstall):
    config = Mock()
    config.get_argument_value.return_value = reinstall
    monkeypatch.setattr(ArgumentParser, "instance", lambda: config)
    commands.return_value = SCOOP_LIST_OUTPUT
    manager = fresh(SoftwareManager)
    commands.reset_mock()
    arguments = Mock(additional_arguments="--skip", install_context=False, run_as_admin=False)

    manager.install("git", arguments)

    expected = [call("scoop uninstall --global git"), call("scoop install --global git --skip"), call("scoop list")]
    assert commands.call_args_list == (expected if reinstall else [])
    config.get_argument_value.assert_called_once_with("reinstall")


def test_updater_reinstalls_each_missing_bucket_once(monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP", r"C:\Scoop")
    commands.side_effect = [
        "Name Version Latest Info\n-----------------------\n"
        "one 1 2 Manifest removed\ntwo 1 2 Manifest removed\nother 2 3\n",
        "",
        "",
    ]
    software = Mock()
    software.get_bucket_name.return_value = "custom"
    monkeypatch.setattr(SoftwareManager, "instance", lambda: software)

    fresh(SoftwareUpdateManager).refresh_scoop_buckets()

    assert software.get_bucket_name.call_args_list == [call("one"), call("two")]
    assert commands.call_args_list == [
        call(r"C:\Scoop\shims\scoop.cmd status --global"),
        call(r"C:\Scoop\shims\scoop.cmd bucket add custom"),
        call(r"C:\Scoop\shims\scoop.cmd update"),
    ]


@pytest.mark.xfail(
    strict=True, raises=subprocess.CalledProcessError, reason="One failed Scoop package aborts the whole update cycle"
)
def test_updater_continues_with_other_packages_after_one_update_fails(monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP", r"C:\Scoop")
    manager = fresh(SoftwareUpdateManager)
    monkeypatch.setattr(manager, "refresh_scoop_buckets", Mock())
    monkeypatch.setattr(manager, "refresh_outdated_software", Mock())
    manager.outdated_software = [("broken", "1", "2"), ("healthy", "3", "4")]
    failed = r"C:\Scoop\shims\scoop.cmd update --global broken"
    healthy = r"C:\Scoop\shims\scoop.cmd update --global healthy"

    def execute(command):
        if command == failed:
            raise subprocess.CalledProcessError(1, command)
        return "Updated"

    commands.side_effect = execute
    notify = Mock()
    monkeypatch.setattr(manager, "send_push_message", notify)
    monkeypatch.setattr(manager, "keep_old_version_of", lambda software: True)

    manager.check_for_updates()

    assert commands.call_args_list == [call(failed), call(healthy)]
    notify.assert_called_once_with("healthy", "3", "4")


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="Scoop inventory skips the last installed app")
def test_scoop_inventory_reads_the_last_installed_app(fresh, commands):
    commands.return_value = SCOOP_LIST_OUTPUT

    manager = fresh(SoftwareManager)

    assert manager.is_installed("git")
    assert manager.is_installed("other")
