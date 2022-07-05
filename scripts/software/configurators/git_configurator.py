import os
from itertools import chain
from pathlib import Path

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.logger import Logger
from scripts.parsers.config_parser import ConfigParser
from scripts.software.configuratorbase import ConfiguratorBase

logger = Logger.instance()


class GitConfigurator(ConfiguratorBase):
    def __init__(self):
        super().__init__(__file__)

        self.global_config = []
        self.global_config_path = os.path.join(str(Path.home()), ".gitconfig")

        self.parse_global_config()

    def parse_global_config(self):
        command = CommandGenerator() \
            .git() \
            .config() \
            .parameters("--global", "--list")

        output = CommandExecutor(print_to_console=len(self.global_config) > 0).execute(command)

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
