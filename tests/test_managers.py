import ctypes
import winreg
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, call

import pytest
import requests
from pushnotifier.PushNotifier import PushNotifier

from scripts.constants.Enums import ExecutablePaths
from scripts.managers import admin_manager, github_file_downloader, network_manager, registry_manager
from scripts.managers.aes_manager import AESManager
from scripts.managers.database_manager import Constant, DatabaseManager
from scripts.managers.explorer_manager import ExplorerManager
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.managers.file_permission_manager import FilePermissionManager
from scripts.managers.push_notifier_manager import PushNotifierManager
from scripts.managers.secret_manager import Secret, SecretManager
from scripts.managers.sha_manager import SHA256Manager
from scripts.managers.string_manager import StringManager
from scripts.managers.windows_notification_manager import WindowsNotificationManager


@pytest.mark.parametrize("is_admin", [0, 1])
def test_admin_manager_reports_windows_token(monkeypatch, fresh, is_admin):
    check = Mock(return_value=is_admin)
    monkeypatch.setattr(ctypes.windll, "shell32", SimpleNamespace(IsUserAnAdmin=check))
    assert bool(fresh(admin_manager.AdminManager).is_user_admin()) is bool(is_admin)
    check.assert_called_once_with()


@pytest.mark.parametrize("sequence_type", [list, tuple])
def test_admin_manager_accepts_explicit_command_line(monkeypatch, fresh, sequence_type):
    launch = Mock(return_value={})
    monkeypatch.setattr(admin_manager, "ShellExecuteEx", launch)
    command_line = sequence_type(("example.exe", "two words"))
    assert fresh(admin_manager.AdminManager).run_as_admin(command_line, wait=False) is None
    assert launch.call_args.kwargs["lpVerb"] == "runas"
    assert launch.call_args.kwargs["lpParameters"] == '"two words"'


@pytest.mark.parametrize("message", ["hello", "sixteen letters!", "A" * 40])
def test_aes_round_trip_and_padding(fresh, message):
    cipher = fresh(AESManager)
    key = "0123456789abcdef"
    encrypted = cipher.encrypt(message, key)
    assert len(encrypted) % 16 == 0
    assert len(encrypted) > len(message)
    assert cipher.decrypt(encrypted, key) == message.encode()


def test_sha256_known_vector(fresh):
    assert fresh(SHA256Manager).hash("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize(("value", "expected"), [("YES", True), ("off", False), ("", False), ("1", True)])
def test_string_manager_boolean_conversion(fresh, value, expected):
    assert fresh(StringManager).str_to_bool(value) is expected


def test_string_manager_converts_sets_and_rejects_invalid_integers(fresh):
    manager = fresh(StringManager)
    assert manager.str_to_set("{one, two, one}") == {"one", "two"}
    assert manager.str_to_int("-3") == -3
    with pytest.raises(ValueError):
        manager.str_to_int("3.14")


def test_database_persists_upsert_and_reports_missing_entry(tmp_path, monkeypatch, fresh):
    monkeypatch.chdir(tmp_path)
    database = fresh(DatabaseManager)
    key = Constant.POWER_SAVINGS_PLAN_GUID
    try:
        assert database.get(key) is None
        database.set(key, "old")
        database.set(key, "new")
    finally:
        database.connection.close()

    reopened = fresh(DatabaseManager)
    try:
        assert reopened.get(key) == "new"
    finally:
        reopened.connection.close()


def test_database_round_trips_values_with_apostrophes(tmp_path, monkeypatch, fresh):
    monkeypatch.chdir(tmp_path)
    database = fresh(DatabaseManager)
    try:
        database.set(Constant.POWER_SAVINGS_PLAN_GUID, "user's plan")
        assert database.get(Constant.POWER_SAVINGS_PLAN_GUID) == "user's plan"
    finally:
        database.connection.close()


def test_explorer_manager_requests_restart_via_powershell(monkeypatch, fresh):
    executor = Mock()
    monkeypatch.setattr("scripts.managers.explorer_manager.CommandExecutor", executor)
    fresh(ExplorerManager).restart()
    executor.assert_called_once_with(is_powershell_command=True)
    command = executor.return_value.execute.call_args.args[0]
    assert command.get() == '-command "gps explorer | spps"'


def test_file_association_manager_parses_known_and_missing_extensions(commands, fresh):
    commands.return_value = ".txt, Editor.File\nhttps, Browser.URL\n"
    associations = fresh(FileAssociationManager)

    assert associations.get(".txt") == "Editor.File"
    assert associations.get("https") == "Browser.URL"
    assert associations.get(".missing") is None
    commands.assert_called_once_with(f"{ExecutablePaths.SET_USER_TFA.to_command()} get")


@pytest.mark.parametrize(("operation", "expected"), [
    ("remove_permission", 'CACLS "test files/key" /e /r user'),
    ("set_read_only", 'icacls "test files/key" /inheritance:r /grant:r user:R'),
    ("set_read_and_write_only", 'icacls "test files/key" /inheritance:r /grant:r user:RW'),
])
def test_file_permissions_quote_path_and_select_access(commands, fresh, operation, expected):
    getattr(fresh(FilePermissionManager), operation)("test files/key", "user")
    commands.assert_called_once_with(expected)


@pytest.mark.parametrize("connection_error", [True, False])
def test_network_manager_handles_connection_errors(monkeypatch, fresh, connection_error):
    head = Mock(side_effect=requests.ConnectionError if connection_error else None)
    monkeypatch.setattr(network_manager.requests, "head", head)
    assert fresh(network_manager.NetworkManager).has_internet_connection() is not connection_error
    head.assert_called_once_with("https://8.8.8.8", timeout=5)


def test_github_downloader_selects_matching_release_asset(monkeypatch, tmp_path, commands, fresh):
    api = "https://api.example.test/latest"
    asset = "https://downloads.example.test/Example_1_x64.zip"
    get = Mock()
    get.return_value.json.return_value = {
        "assets": [{"browser_download_url": "https://downloads.example.test/checksums.txt"},
                   {"browser_download_url": asset}]
    }
    monkeypatch.setattr(github_file_downloader.requests, "get", get)
    destination = tmp_path / "releases"

    assert fresh(github_file_downloader.GithubFileDownloader).download(api, destination, r"Example_.*_x64.zip") == (
        "Example_1_x64.zip"
    )
    assert destination.is_dir()
    get.assert_called_once_with(url=api)
    commands.assert_called_once_with(f"wget --no-clobber -P {destination} {asset}")


def test_github_downloader_skips_existing_exact_filename(monkeypatch, tmp_path, commands, fresh):
    (tmp_path / "tool.zip").touch()
    get = Mock()
    monkeypatch.setattr(github_file_downloader.requests, "get", get)

    fresh(github_file_downloader.GithubFileDownloader).download("https://example.test/latest", tmp_path, "tool.zip")

    get.assert_not_called()
    commands.assert_not_called()


def test_push_notifier_loads_fixture_credentials_and_forwards_device_selection(monkeypatch, tmp_path, fresh):
    path = tmp_path / "notification.ini"
    path.write_text("[CREDENTIALS]\nusername=u\npassword=p\npackage_name=example\napi_key=fixture\n", encoding="ascii")
    initialize = Mock(return_value=None)
    send = Mock()
    monkeypatch.setattr(PushNotifier, "__init__", initialize)
    monkeypatch.setattr(PushNotifier, "send_text", send)
    monkeypatch.setattr(PushNotifierManager._decorated, "CONFIG_FILEPATH", path)

    notifier = fresh(PushNotifierManager)
    notifier.send_text("message", ["phone"], silent=True)

    initialize.assert_called_once_with(notifier, "u", "p", "example", "fixture")
    send.assert_called_once_with(notifier, "message", ["phone"], True)


def test_windows_notification_forwards_to_toast_provider(monkeypatch, fresh):
    notifier = fresh(WindowsNotificationManager)
    toast = Mock()
    monkeypatch.setattr(notifier, "show_toast", toast)

    notifier.send("Title", "Body", "icon.ico", 3, True)

    toast.assert_called_once_with("Title", "Body", "icon.ico", 3, True)


@pytest.mark.parametrize("encrypted", [False, True])
def test_secret_manager_runs_only_necessary_git_crypt_operation(tmp_path, monkeypatch, commands, fresh, encrypted):
    monkeypatch.chdir(tmp_path)
    secret = tmp_path / Secret.PRIVATE_KEY_OPENSSH.value
    secret.parent.mkdir(parents=True)
    secret.write_bytes(b"\x00GITCRYPTpayload" if encrypted else b"fixture plaintext")
    key = tmp_path / "fixture.key"
    key.write_bytes(b"\x00GITCRYPTKEYfixture")
    manager = fresh(SecretManager)

    assert manager.is_git_cryptkey(key)
    assert manager.is_encrypted(Secret.PRIVATE_KEY_OPENSSH) is encrypted
    manager.unlock()
    manager.lock()

    commands.assert_called_once_with("git-crypt unlock secret_decrypted" if encrypted else "git-crypt lock")


@pytest.mark.parametrize(("existing", "creates_key", "writes_entry"), [
    (None, True, True),
    (7, False, False),
    (3, False, True),
])
def test_registry_creates_missing_key_and_avoids_redundant_writes(monkeypatch, fresh, existing, creates_key, writes_entry):
    client_factory = MagicMock()
    client = client_factory.return_value.__enter__.return_value
    if existing is None:
        client.read_key.side_effect = FileNotFoundError
        client.read_entry.side_effect = FileNotFoundError
    else:
        client.read_entry.return_value = SimpleNamespace(value=existing)
    monkeypatch.setattr(registry_manager, "WinRegistry", client_factory)
    manager = fresh(registry_manager.RegistryManager)
    key = registry_manager.RegistryPath.WINDOWS_ROOT_APPLICATIONS_COMMAND
    path = r"HKEY_CLASSES_ROOT\Editor.File\shell\open\command"

    assert key.get_path("Editor.File") == path
    assert key.get_registry_key() == ""
    assert manager.get(key, "Editor.File") == existing
    manager.set(key, 7, winreg.REG_DWORD, "Editor.File")

    assert client.create_key.call_args_list == ([call(path)] if creates_key else [])
    assert client.write_entry.call_args_list == ([call(path, "", 7, winreg.REG_DWORD)] if writes_entry else [])


def test_registry_bulk_set_preserves_value_types(monkeypatch, fresh):
    manager = fresh(registry_manager.RegistryManager)
    write = Mock()
    monkeypatch.setattr(manager, "set", write)
    keys = registry_manager.RegistryPath
    manager.set_all({
        keys.UAC_ENABLE_LUA: 0,
        keys.JETBRAINS_EULA_VERSION: "1.4",
        keys.WINDOWS_BACKGROUND_COLOR: ("%VALUE%", winreg.REG_EXPAND_SZ),
    })
    assert write.call_args_list == [
        call(keys.UAC_ENABLE_LUA, 0, winreg.REG_DWORD),
        call(keys.JETBRAINS_EULA_VERSION, "1.4", winreg.REG_SZ),
        call(keys.WINDOWS_BACKGROUND_COLOR, "%VALUE%", winreg.REG_EXPAND_SZ),
    ]
