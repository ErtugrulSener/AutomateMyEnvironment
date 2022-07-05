import os
from itertools import chain
from pathlib import Path

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton
from scripts.software.configurator_base import ConfiguratorBase

logger = Logger.instance()


@Singleton
class GitConfigurator(ConfiguratorBase):
    def __init__(self):
        super().__init__(__file__)

        self.global_config = []
        self.global_config_path = os.path.join(str(Path.home()), ".gitconfig")

        self.load_global_config()

    def load_global_config(self):
        command = CommandGenerator() \
            .git() \
            .config() \
            .parameters("--global", "--list")
        output = CommandExecutor(print_to_console=logger.is_trace()).execute(command)

        for line in output.splitlines():
            key, value = line.split("=")
            self.global_config.append((key, value))

    def is_config_set(self, searched_key):
        for config_key, _ in chain(self.global_config):
            if config_key == searched_key:
                return True

        return False

    def is_configured_already(self):
        for key, value in ConfigParser.instance().items("GIT"):
            if not self.is_config_set(key):
                return False

        return True

    def configure(self):
        logger.info(f"Found global config file in path: {self.global_config_path}")
        logger.info(f"Checking if there are config parameters that need to be updated...")

        for key, value in ConfigParser.instance().items("GIT"):
            if not self.is_config_set(key):
                self.info(f"Setting key '{key}' to value '{value}'")

                command = CommandGenerator() \
                    .git() \
                    .config("--global") \
                    .parameters(key, value)
                CommandExecutor().execute(command)
