from unittest.mock import Mock

import pytest

from scripts.commands.command_executor import CommandExecutor


@pytest.fixture
def fresh(monkeypatch):
    def instance(singleton):
        monkeypatch.setattr(singleton, "_instance", None)
        return singleton.instance()

    return instance


@pytest.fixture
def commands(monkeypatch):
    execute = Mock(return_value="")

    def capture(self, command):
        return execute(command.get())

    monkeypatch.setattr(CommandExecutor, "execute", capture)
    return execute
