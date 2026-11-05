import ctypes
import os
import winreg
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest
import win32api

from scripts.configurators.windows.windows_autostart_configurator import WindowsAutostartConfigurator
from scripts.configurators.windows.windows_dark_mode_configurator import WindowsDarkModeConfigurator
from scripts.configurators.windows.windows_default_browser_configurator import WindowsDefaultBrowserConfigurator
from scripts.configurators.windows.windows_desktop_configurator import WindowsDesktopConfigurator
from scripts.configurators.windows.windows_desktop_icon_configurator import WindowsDesktopIconConfigurator
from scripts.configurators.windows.windows_energy_saving_plan_configurator import PowerConfiguration
from scripts.configurators.windows.windows_energy_saving_plan_configurator import WindowsEnergySavingPlanConfigurator
from scripts.configurators.windows.windows_file_association_configurator import WindowsFileAssociationConfigurator
from scripts.configurators.windows.windows_folder_options_configurator import WindowsFolderOptionsConfigurator
from scripts.configurators.windows.windows_screen_resolution_configurator import WindowsScreenResolutionConfigurator
from scripts.configurators.windows.windows_ssh_credentials_configurator import WindowsSSHCredentialsConfigurator
from scripts.configurators.windows.windows_taskbar_configurator import WindowsTaskbarConfigurator
from scripts.configurators.windows.windows_uac_configurator import WindowsUACConfigurator
from scripts.constants.Enums import ExecutablePaths
from scripts.managers.database_manager import Constant, DatabaseManager
from scripts.managers.explorer_manager import ExplorerManager
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.parsers.config_parser import ConfigParser

# WindowsServicesConfigurator creates its WMI client at class definition.
with patch("wmi.WMI"):
    from scripts.configurators.windows.windows_defender_configurator import WindowsDefenderConfigurator
    from scripts.configurators.windows.windows_services_configurator import ServiceStartType, ServiceStatus
    from scripts.configurators.windows.windows_services_configurator import WindowsServicesConfigurator


@pytest.fixture
def registry(monkeypatch):
    client = Mock()
    monkeypatch.setattr(RegistryManager, "instance", lambda: client)
    return client


@pytest.mark.parametrize("configurator_type", [
    WindowsDarkModeConfigurator,
    WindowsDesktopIconConfigurator,
    WindowsFolderOptionsConfigurator,
    WindowsUACConfigurator,
])
@pytest.mark.parametrize("already_configured", [True, False])
def test_registry_configurators_only_write_when_settings_differ(registry, fresh, configurator_type, already_configured):
    registry.check_all.return_value = already_configured
    configurator = fresh(configurator_type)

    assert configurator.is_configured_already() is already_configured
    configurator.configure()

    expected = [] if already_configured else [call(configurator.EXPECTED_REGISTRY_ENTRIES)]
    assert registry.set_all.call_args_list == expected


def test_autostart_filters_and_deduplicates_enabled_run_entries(registry, fresh, commands):
    run_key = r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    commands.return_value = (
        "Entry Location\tPath\tName\tEnabled\n"
        f"\t{run_key}\tEnabledApp\tenabled\n"
        f"\t{run_key}\tEnabledApp\tenabled\n"
        f"\t{run_key}\tDisabledApp\tdisabled\n"
        f"\t{run_key}Once\tRunOnceApp\tenabled\n"
    )
    registry.get_entry.return_value = SimpleNamespace(value="example.exe", type=winreg.REG_SZ)

    configurator = fresh(WindowsAutostartConfigurator)
    assert not configurator.is_configured_already()
    configurator.configure()

    registry.delete_entry.assert_called_once_with(run_key, "EnabledApp")
    registry.set_entry.assert_called_once_with(
        run_key + r"\AutorunsDisabled", "EnabledApp", "example.exe", winreg.REG_SZ
    )


def test_default_browser_keeps_registered_identifier_suffix(fresh, commands):
    commands.return_value = "HKLM Brave.Fixture\n  name: Brave\n  path: example.exe\n"
    configurator = fresh(WindowsDefaultBrowserConfigurator)
    assert configurator.find_default_type_browser_by_identifier("Brave") == ("HKLM", "Brave.Fixture")
    assert configurator.find_default_type_browser_by_identifier("Missing") is None

    configurator.set_default_browser("Brave")

    assert commands.call_args_list[-1] == call(f"{ExecutablePaths.SET_DEFAULT_BROWSER.to_command()} HKLM Brave.Fixture")


@pytest.mark.parametrize(("status", "correct_settings", "expected"), [
    (ServiceStatus.RUNNING, True, False),
    (ServiceStatus.STOPPED, False, False),
    (ServiceStatus.STOPPED, True, True),
])
def test_defender_configuration_requires_stopped_service_and_registry_setting(
        monkeypatch, registry, fresh, status, correct_settings, expected):
    services = Mock()
    services.get_status.return_value = status
    registry.check_all.return_value = correct_settings
    monkeypatch.setattr(WindowsServicesConfigurator, "instance", lambda: services)

    assert fresh(WindowsDefenderConfigurator).is_configured_already() is expected
    services.get_status.assert_called_once_with("WinDefend")


@pytest.mark.parametrize(("windows_color", "is_configured"), [(0, True), (0x123456, False)])
def test_desktop_checks_background_without_changing_windows(monkeypatch, fresh, windows_color, is_configured):
    user32 = Mock()
    user32.GetSysColor.return_value = windows_color
    monkeypatch.setattr(ctypes.windll, "user32", user32)
    configurator = fresh(WindowsDesktopConfigurator)
    monkeypatch.setattr(configurator, "has_wallpaper", lambda: False)

    assert configurator.is_configured_already() is is_configured
    if not is_configured:
        assert configurator.get_background_color() == [0x12, 0x34, 0x56]


def test_power_plan_reuses_saved_guid_and_parses_hex_settings(monkeypatch, registry, fresh, commands):
    guid = "12345678-abcd-1234-abcd-123456789abc"
    database = Mock()
    database.get.return_value = guid
    monkeypatch.setattr(DatabaseManager, "instance", lambda: database)
    commands.side_effect = [
        f"Power plans\n-----------\n\nPower Scheme GUID: {guid} (Fixture) *\n",
        "Current AC Power Setting Index: 0x0000000a\nCurrent DC Power Setting Index: 0x00000005\n\n",
        "",
        "",
        "",
    ]
    registry.get.return_value = 2

    configurator = fresh(WindowsEnergySavingPlanConfigurator)

    assert configurator.TARGET_GUID == guid
    assert configurator.power_configurations == {guid: True}
    assert configurator.get_setting_value("SUB_VIDEO", "VIDEOIDLE", 0) == (10, 5)
    assert not configurator.is_configured_already()
    database.get.assert_called_once_with(Constant.POWER_SAVINGS_PLAN_GUID)
    database.set.assert_not_called()
    assert configurator.TARGET_GUID != PowerConfiguration.TOP_PERFORMANCE.value
    assert len(commands.call_args_list) == 5


def test_file_association_writes_command_and_updates_default(monkeypatch, registry, commands, fresh):
    config = fresh(ConfigParser)
    config.read_dict({"WINDOWS-FILE-ASSOCIATIONS": {".txt": "--prog-id Editor.File --command editor.exe %1"}})
    registry.get.return_value = "old.exe %1"
    associations = Mock()
    associations.get.return_value = "Other.File"
    monkeypatch.setattr(FileAssociationManager, "instance", lambda: associations)

    configurator = fresh(WindowsFileAssociationConfigurator)
    assert not configurator.is_configured_already()
    configurator.configure()

    registry.set.assert_called_once_with(
        RegistryPath.WINDOWS_ROOT_APPLICATIONS_COMMAND, "editor.exe %1", winreg.REG_SZ, "Editor.File"
    )
    commands.assert_called_once_with(f"{ExecutablePaths.SET_USER_TFA.to_command()} .txt Editor.File")


def test_screen_resolution_uses_highest_available_refresh_rate(monkeypatch, fresh, commands):
    device = r"\\.\DISPLAY1"
    monkeypatch.setattr(win32api, "EnumDisplayMonitors", lambda: [(42,)])
    monkeypatch.setattr(win32api, "GetMonitorInfo", lambda handle: {"Device": device})
    monkeypatch.setattr(win32api, "EnumDisplaySettings", lambda device, index: SimpleNamespace(DisplayFrequency=60))
    commands.return_value = "Modes:\n1920x1080 32bit @60Hz default\n1920x1080 32bit @144Hz supported\n"

    configurator = fresh(WindowsScreenResolutionConfigurator)
    assert configurator.get_highest_possible_refresh_rate(device) == 144
    assert not configurator.is_configured_already()
    configurator.configure()

    executable = ExecutablePaths.CHANGE_SCREEN_RESOLUTION.to_command()
    assert commands.call_args_list == [
        call(f"{executable} /m /d={device}"),
        call(f"{executable} /d={device} /f=144"),
    ]


@pytest.mark.parametrize("running", [True, False])
def test_services_configurator_accepts_wmi_auto_alias_and_only_starts_stopped_service(monkeypatch, fresh, running):
    config = fresh(ConfigParser)
    config.read_dict({"WINDOWS-SERVICES": {"FixtureService": "--start-mode Automatic --action start"}})
    service = Mock(StartMode="Auto", State="Running" if running else "Stopped")
    service.StartService.return_value = 0
    wmi = Mock()
    wmi.Win32_Service.return_value = [service]
    configurator = fresh(WindowsServicesConfigurator)
    monkeypatch.setattr(configurator, "wmi", wmi)

    assert configurator.get_start_mode("FixtureService") is ServiceStartType.AUTOMATIC
    assert configurator.is_configured_already() is running
    configurator.configure()

    service.ChangeStartMode.assert_not_called()
    assert service.StartService.call_count == int(not running)
    service.StopService.assert_not_called()


def test_ssh_configurator_skips_agent_update_for_loaded_key_and_copies_fixture_directory(
        tmp_path, monkeypatch, fresh, commands):
    source = tmp_path / "source"
    source.mkdir()
    (source / "public.pub").write_text("fixture public key", encoding="ascii")
    destination = tmp_path / "destination"
    configurator_type = WindowsSSHCredentialsConfigurator._decorated
    monkeypatch.setattr(configurator_type, "KEYS_FOLDER_PATH", source)
    monkeypatch.setattr(configurator_type, "LOCAL_KEYS_FOLDER_PATH", destination)
    commands.return_value = f"ssh-rsa {configurator_type.PUBLIC_KEY} test@example.test\n"

    configurator = fresh(WindowsSSHCredentialsConfigurator)
    assert not configurator.is_configured_already()
    configurator.configure()
    assert configurator.is_configured_already()

    assert (destination / "public.pub").read_text(encoding="ascii") == "fixture public key"
    commands.assert_called_once_with("ssh-add -L")


def test_taskbar_removes_pins_and_restarts_explorer_only_when_needed(tmp_path, monkeypatch, registry, fresh):
    pin = tmp_path / "example.lnk"
    pin.touch()
    explorer = Mock()
    monkeypatch.setattr(ExplorerManager, "instance", lambda: explorer)
    configurator = fresh(WindowsTaskbarConfigurator)
    monkeypatch.setattr(configurator, "USER_PINNED_QUICK_LAUNCH_PATH", os.fspath(tmp_path))

    registry.check_all.return_value = True
    configurator.configure()
    assert pin.exists()
    explorer.restart.assert_not_called()

    registry.check_all.return_value = False
    configurator.configure()
    assert not pin.exists()
    registry.delete_tree.assert_called_once_with(RegistryPath.WINDOWS_EXPLORER_TASKBAND)
    explorer.restart.assert_called_once_with()
