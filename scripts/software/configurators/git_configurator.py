import os
import subprocess
from itertools import chain

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.parsers.config_parser import ConfigParser
from scripts.software.configurator import Configurator

from pathlib import Path
from scripts.logger import Logger

logger = Logger.instance()


class GitConfigurator(Configurator):
    def __init__(self):
        super().__init__(__file__)
        self.global_config = []
        self.global_config_path = os.path.join(str(Path.home()), ".gitconfig")

        self.parse_global_config()
        self.is_config_set("core.sshcommand")

    def parse_global_config(self):
        command = CommandGenerator() \
            .git() \
            .config() \
            .parameters("--global", "--list")

        output = CommandExecutor.instance().get_output(command)

        for line in output.splitlines():
            key, value = line.split("=")
            self.global_config.append((key, value))

    def is_config_set(self, searched_key):
        for config_key, _ in chain(self.global_config):
            if config_key == searched_key:
                return True

        return False

    def all_set_already(self):
        for key, value in ConfigParser.instance().items("GIT"):
            if not self.is_config_set(key):
                return False;

        return True

    def configure(self):
        if self.all_set_already():
            self.skip()
            return

        logger.info(f"Found global config file in path: {self.global_config_path}")
        logger.info(f"Checking if there are config parameters that need to be updated...")

        for key, value in ConfigParser.instance().items("GIT"):
            if not self.is_config_set(key):
                self.info(f"Setting key '{key}' to value '{value}'")

                command = CommandGenerator() \
                    .git() \
                    .config("--global") \
                    .parameters(key, value)

                subprocess.run(command.get())
