import json
import os
import winreg
import zipfile
from unittest.mock import Mock, call

import pytest

from scripts.configurators.software.brave_configurator import BraveConfigurator
from scripts.configurators.software.cmder_configurator import CmderConfigurator
from scripts.configurators.software.git_configurator import GitConfigurator
from scripts.configurators.software.intellij_configurator import IntelliJConfigurator
from scripts.configurators.software.notepadplusplus_configurator import NotepadPlusPlusConfigurator
from scripts.configurators.software.putty_configurator import PuttyConfigurator
from scripts.configurators.software.pycharm_configurator import PyCharmConfigurator
from scripts.configurators.software.winscp_configurator import WinscpConfigurator
from scripts.managers.github_file_downloader import GithubFileDownloader
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.parsers.config_parser import ConfigParser


def test_brave_creates_first_run_marker_once(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    user_data = tmp_path / "persist" / "brave" / "User Data"
    user_data.mkdir(parents=True)
    fresh(SoftwareManager)
    configurator = fresh(BraveConfigurator)

    assert not configurator.is_configured_already()
    configurator.configure()
    assert configurator.is_configured_already()
    marker = user_data / "First Run"
    marker.write_text("existing", encoding="ascii")
    configurator.configure()
    assert marker.read_text(encoding="ascii") == "existing"


def test_cmder_compares_payload_after_generated_header(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    settings = tmp_path / "external" / "configurations" / "cmder" / "ConEmu.xml"
    settings.parent.mkdir(parents=True)
    settings.write_text("one\ntwo\nthree\nfour\n<same />\n", encoding="utf-8")
    target = tmp_path / "apps" / "cmder" / "current" / "vendor" / "conemu-maximus5" / "ConEmu.xml"
    target.parent.mkdir(parents=True)
    fresh(SoftwareManager)
    registry = Mock()
    registry.get.return_value = None
    monkeypatch.setattr(RegistryManager, "instance", lambda: registry)
    configurator = fresh(CmderConfigurator)

    assert not configurator.has_right_settings()
    configurator.configure()
    assert target.read_bytes() == settings.read_bytes()
    target.write_text("a\nb\nc\nd\n<same />\n", encoding="utf-8")
    assert configurator.has_right_settings()
    assert registry.set.call_count == 6
    registry.set.assert_any_call(
        RegistryPath.WINDOWS_LEFT_PANEL_COMMAND, f'"{configurator.executable_path}" "%V"', winreg.REG_SZ, "cmder"
    )


def test_git_configurator_only_adds_missing_keys(fresh, commands):
    config = fresh(ConfigParser)
    config.read_dict({"GIT": {"user.name": "Fixture Name", "core.autocrlf": "false"}})
    commands.return_value = "user.name=Existing User\n"

    configurator = fresh(GitConfigurator)
    assert not configurator.is_configured_already()
    configurator.configure()

    assert commands.call_args_list == [
        call("git config --global --list"),
        call('git config --global core.autocrlf "false"'),
    ]


@pytest.mark.xfail(strict=True, raises=ValueError, reason="GitConfigurator splits on every equals sign")
def test_git_configurator_accepts_equals_in_existing_value(fresh, commands):
    commands.return_value = "http.extraheader=X-Custom=enabled\n"
    assert fresh(GitConfigurator).is_config_set("http.extraheader")


def test_intellij_requires_all_license_files_in_product_config_directory(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("APPDATA", str(tmp_path / "profile"))
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    product_info = tmp_path / "apps" / "idea" / "current" / "IDE" / "product-info.json"
    product_info.parent.mkdir(parents=True)
    product_info.write_text(json.dumps({"dataDirectoryName": "FixtureIdea"}), encoding="utf-8")
    fresh(SoftwareManager)
    configurator = fresh(IntelliJConfigurator)
    config_directory = tmp_path / "profile" / "JetBrains" / "FixtureIdea"

    assert configurator.get_config_folder_path() == os.fspath(config_directory)
    assert not configurator.is_licensed()
    config_directory.mkdir(parents=True)
    (config_directory / "idea.key").touch()
    assert not configurator.is_licensed()
    (config_directory / "plugin_PCWMP.license").touch()
    assert configurator.is_licensed()
    assert not configurator.has_settings_repository()
    (config_directory / "settingsRepository").mkdir()
    assert configurator.has_settings_repository()


def test_notepadplusplus_extracts_missing_plugin_and_skips_installed(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    archive = tmp_path / "ComparePlus_1_x64.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("ComparePlus.dll", b"fixture")
    downloader = Mock()
    downloader.download.return_value = archive.name
    monkeypatch.setattr(GithubFileDownloader, "instance", lambda: downloader)
    monkeypatch.setattr(NotepadPlusPlusConfigurator._decorated, "NOTEPADPLUSPLUS_LOCAL_PATH", tmp_path)
    fresh(SoftwareManager)
    configurator = fresh(NotepadPlusPlusConfigurator)

    assert not configurator.is_configured_already()
    configurator.configure()
    assert configurator.is_configured_already()
    configurator.configure()

    plugin = tmp_path / "apps" / "notepadplusplus" / "current" / "plugins" / "ComparePlus" / "ComparePlus.dll"
    assert plugin.read_bytes() == b"fixture"
    downloader.download.assert_called_once()


@pytest.mark.parametrize("configured", [True, False])
def test_putty_only_writes_missing_registry_settings(monkeypatch, fresh, configured):
    registry = Mock()
    registry.check_all.return_value = configured
    monkeypatch.setattr(RegistryManager, "instance", lambda: registry)
    configurator = fresh(PuttyConfigurator)

    assert configurator.is_configured_already() is configured
    configurator.configure()

    assert registry.set_all.call_args_list == ([] if configured else [call(configurator.EXPECTED_REGISTRY_ENTRIES)])


@pytest.mark.parametrize("version", [None, "1.0"])
def test_pycharm_only_writes_missing_eula_version(monkeypatch, fresh, version):
    registry = Mock()
    registry.get.return_value = version
    monkeypatch.setattr(RegistryManager, "instance", lambda: registry)
    configurator = fresh(PyCharmConfigurator)

    assert configurator.is_configured_already() is (version == "1.0")
    configurator.configure()

    assert registry.set.call_args_list == (
        [call(RegistryPath.JETBRAINS_COMMUNITY_EULA_VERSION, "1.0")] if version is None else []
    )


def test_winscp_loads_configuration_and_detects_existing_setting(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    config = tmp_path / "apps" / "winscp" / "current" / "winscp.ini"
    config.parent.mkdir(parents=True)
    config.write_text("[Configuration\\Interface]\nShowHiddenFiles=1\n", encoding="ascii")
    fresh(SoftwareManager)

    assert fresh(WinscpConfigurator).is_configured_already()


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="WinSCP mutates the same config object it compares")
def test_winscp_saves_changes_for_the_next_run(tmp_path, monkeypatch, fresh, commands):
    monkeypatch.setenv("SCOOP_GLOBAL", str(tmp_path))
    config = tmp_path / "apps" / "winscp" / "current" / "winscp.ini"
    config.parent.mkdir(parents=True)
    config.write_text("[Unrelated]\nKeepMe=yes\n", encoding="ascii")
    fresh(SoftwareManager)
    configurator = fresh(WinscpConfigurator)
    assert not configurator.is_configured_already()

    configurator.configure()

    reopened = fresh(WinscpConfigurator)
    assert reopened.winscp_configuration.get("Unrelated", "KeepMe") == "yes"
    assert reopened.is_configured_already()
