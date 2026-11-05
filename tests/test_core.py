import base64
import logging
import os
import subprocess
import sys
from unittest.mock import MagicMock, Mock, call

import pytest

from scripts.checkers import alias_checker, secrets_checker, system_checker
from scripts.checkers.checker import Checker
from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator import Configurator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import Color, ExecutablePaths
from scripts.logging.logger import FileHandler, Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.parsers.parser import Parser
from scripts.singleton import Singleton


def test_singleton_constructs_once_and_requires_instance_method():
    constructor = Mock(return_value=object())
    singleton = Singleton(constructor)

    constructor.assert_not_called()
    assert singleton.instance() is singleton.instance()
    constructor.assert_called_once_with()
    with pytest.raises(TypeError, match="instance"):
        singleton()


def test_command_generator_composes_and_resets():
    generator = CommandGenerator().git().config("--global").parameters("user.name", '"Test User"')
    generator += CommandGenerator().pipe().findstr().parameters("name", "__ignored")
    assert generator.get() == 'git config --global user.name "Test User" | findstr name'
    assert generator.status().get() == "status"


@pytest.mark.parametrize("return_code", [0, 3, 7])
def test_command_executor_decodes_output_and_handles_exit_codes(monkeypatch, return_code):
    process = Mock(stdout=iter(["\x1b[32mGrün\x1b[0m\n"]), returncode=return_code, args="powershell example")
    popen = MagicMock()
    popen.return_value.__enter__.return_value = process
    monkeypatch.setattr(subprocess, "Popen", popen)
    executor = CommandExecutor(is_powershell_command=True, expected_return_codes=[3], fetch_exit_code=True)

    if return_code == 7:
        with pytest.raises(subprocess.CalledProcessError) as raised:
            executor.execute(CommandGenerator().example())
        assert raised.value.returncode == 7
        assert raised.value.cmd == "powershell example"
    else:
        assert executor.execute(CommandGenerator().example()) == ("Grün\n", return_code)

    assert popen.call_args.kwargs["args"] == "powershell example"
    assert popen.call_args.kwargs["encoding"] == "cp850"
    process.wait.assert_called_once_with()


def test_executable_path_is_quoted_in_a_directory_with_spaces(tmp_path, monkeypatch):
    directory = tmp_path / "Automation folder"
    directory.mkdir()
    monkeypatch.chdir(directory)

    expected = directory / "external" / "executables" / "autoruns" / "autorunsc64.exe"
    assert ExecutablePaths.AUTORUNS.to_command() == f'"{expected}"'
    assert Color.YELLOW.value() == "yellow"


@pytest.mark.parametrize("https_proxy", [None, "http://secure.example.test:8080"])
def test_argument_parser_sets_proxy_and_reinstall(monkeypatch, fresh, https_proxy):
    http_proxy = "http://proxy.example.test:8080"
    arguments = ["install.py", "--reinstall", "--http-proxy", http_proxy]
    if https_proxy:
        arguments.extend(["--https-proxy", https_proxy])
    monkeypatch.setattr(sys, "argv", arguments)
    for name in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY"):
        monkeypatch.delenv(name, raising=False)

    parser = fresh(ArgumentParser)
    parser.parse()

    assert parser.get_argument_value("reinstall") is True
    assert os.environ["http_proxy"] == os.environ["HTTP_PROXY"] == http_proxy
    assert os.environ["https_proxy"] == os.environ["HTTPS_PROXY"] == (https_proxy or http_proxy)


def test_config_parser_keeps_case_and_interpolates(tmp_path, monkeypatch, fresh):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.ini").write_text(
        "[Paths]\nRoot = tools\n[Options]\nTool = ${Paths:Root}/example ; inline comment\n", encoding="ascii"
    )
    config = fresh(ConfigParser)
    config.parse()
    assert dict(config.items("Options")) == {"Tool": "tools/example"}


@pytest.mark.parametrize(("dispatcher", "method", "collection"), [
    (Checker, "check", "checkers"),
    (Parser, "parse", "parsers"),
])
def test_dispatchers_run_again_without_recording_duplicate_instances(monkeypatch, fresh, dispatcher, method, collection):
    instance = fresh(dispatcher)
    monkeypatch.setattr(instance, collection, [])
    target = Mock()
    target_type = Mock()
    target_type.instance.return_value = target

    getattr(instance, method)(target_type)
    getattr(instance, method)(target_type)

    assert getattr(instance, collection) == [target]
    assert getattr(target, method).call_args_list == [call(), call()]


@pytest.mark.parametrize("configured", [True, False])
def test_configurator_dispatches_skip_or_apply(monkeypatch, fresh, configured):
    target = Mock()
    target.get_name.return_value = "example"
    target.is_configured_already.return_value = configured
    target_type = Mock()
    target_type.instance.return_value = target
    dispatcher = fresh(Configurator)
    monkeypatch.setattr(dispatcher, "configurators", [])

    dispatcher.configure(target_type)

    assert dispatcher.configurators == [target]
    assert target.skip.call_count == int(configured)
    assert target.configure.call_count == int(not configured)


def test_configurator_base_derives_name():
    assert ConfiguratorBase("scripts/example_tool_configurator.py").get_name() == "example_tool"


def test_logger_updates_handlers_and_strips_color_from_file(tmp_path, fresh):
    logger = fresh(Logger)
    log_file = tmp_path / "example.log"
    handler = FileHandler(log_file, encoding="utf-8")
    logger.addHandler(handler)
    try:
        logger.set_log_level("trace")
        assert logger.is_trace()
        assert handler.level == logging.TRACE
        logger.info("\x1b[32mcolored text\x1b[0m")
        logger.set_log_level(logging.DEBUG)
        assert logger.is_debug()
    finally:
        logger.removeHandler(handler)
        handler.close()

    contents = log_file.read_text(encoding="utf-8")
    assert "colored text" in contents
    assert "\x1b" not in contents


def test_alias_checker_persists_and_reuses_default(tmp_path, monkeypatch, fresh):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ALIAS", raising=False)
    monkeypatch.setattr(alias_checker.platform, "node", lambda: "test-machine")
    monkeypatch.setattr(alias_checker.os, "getlogin", lambda: "test-user")
    prompt = Mock(return_value="")
    monkeypatch.setattr("builtins.input", prompt)

    checker = fresh(alias_checker.AliasChecker)
    checker.check()
    checker.check()

    assert (tmp_path / "alias").read_text() == "test-machine"
    assert alias_checker.os.environ["ALIAS"] == "test-machine"
    prompt.assert_called_once()


@pytest.mark.parametrize("failure", ["admin", "platform", "dependency", "tamper", "network", None])
def test_system_checker_reports_the_failed_precondition(monkeypatch, fresh, failure):
    admin = Mock()
    admin.is_user_admin.return_value = failure != "admin"
    registry = Mock()
    registry.get.return_value = 1 if failure == "tamper" else 4
    network = Mock()
    network.has_internet_connection.return_value = failure != "network"
    monkeypatch.setattr(system_checker.AdminManager, "instance", lambda: admin)
    monkeypatch.setattr(system_checker.RegistryManager, "instance", lambda: registry)
    monkeypatch.setattr(system_checker.NetworkManager, "instance", lambda: network)
    monkeypatch.setattr(system_checker.platform, "win32_ver", lambda: () if failure == "platform" else ("11",))
    monkeypatch.setattr(system_checker, "which", lambda name: None if failure == "dependency" else name)

    checker = fresh(system_checker.SystemChecker)
    codes = {"admin": 1, "platform": 2, "dependency": 3, "tamper": 5, "network": 6}
    if failure:
        with pytest.raises(SystemExit) as raised:
            checker.check()
        assert raised.value.code == codes[failure]
    else:
        checker.check()
        network.has_internet_connection.assert_called_once_with()


@pytest.mark.parametrize("existing_key", [True, False])
def test_secrets_checker_reuses_or_decrypts_key(tmp_path, monkeypatch, fresh, existing_key):
    monkeypatch.chdir(tmp_path)
    encrypted = tmp_path / "secret"
    decrypted = tmp_path / "secret_decrypted"
    encrypted.write_bytes(b"encrypted fixture")
    if existing_key:
        decrypted.write_bytes(b"existing key")

    secrets = Mock()
    secrets.is_git_cryptkey.return_value = True
    aes = Mock()
    aes.decrypt.return_value = base64.b64encode(b"synthetic key")
    prompt = Mock(return_value="fixture password")
    monkeypatch.setattr(secrets_checker.SecretManager, "instance", lambda: secrets)
    monkeypatch.setattr(secrets_checker.AESManager, "instance", lambda: aes)
    monkeypatch.setattr(secrets_checker.pwinput, "pwinput", prompt)

    fresh(secrets_checker.SecretsChecker).check()

    secrets.unlock.assert_called_once_with()
    if existing_key:
        assert decrypted.read_bytes() == b"existing key"
        prompt.assert_not_called()
        aes.decrypt.assert_not_called()
    else:
        assert decrypted.read_bytes() == b"synthetic key"
        aes.decrypt.assert_called_once_with(b"encrypted fixture", "fixture password")


def test_secrets_checker_rejects_invalid_password_without_writing_key(tmp_path, monkeypatch, fresh):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "secret").write_bytes(b"encrypted fixture")
    aes = Mock()
    aes.decrypt.side_effect = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
    monkeypatch.setattr(secrets_checker.AESManager, "instance", lambda: aes)
    monkeypatch.setattr(secrets_checker.pwinput, "pwinput", lambda **kwargs: "bad password")

    with pytest.raises(SystemExit) as raised:
        fresh(secrets_checker.SecretsChecker).check()

    assert raised.value.code == 8
    assert not (tmp_path / "secret_decrypted").exists()
