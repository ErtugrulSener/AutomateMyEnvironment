import os

from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton


@Singleton
class WindowsFileAssociationConfigurator(ConfiguratorBase):
    SET_USER_FTA_LOCAL_PATH = os.path.join(os.getcwd(), r"external/executables/set-user-fta/SetUserFTA.exe")

    def __init__(self):
        super().__init__(__file__)

        self.associated_file_extensions = {}
        self.load_associated_file_extensions()

    def load_associated_file_extensions(self):
        command = CommandGenerator() \
            .parameters(self.SET_USER_FTA_LOCAL_PATH, "get")

        output = CommandExecutor().execute(command)

        for line in output.splitlines():
            extension, association = line.split(", ")
            self.associated_file_extensions[extension] = association

    def get(self, extension):
        return self.associated_file_extensions.get(extension)

    def is_configured_already(self):
        for extension, prog_id in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            if self.get(extension) != prog_id:
                return False

        return True

    def configure(self):
        for extension, prog_id in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            if self.get(extension) != prog_id:
                self.info(f"Setting prog id for [{colored(extension, 'yellow')}] to [{colored(prog_id, 'yellow')}]")

                command = CommandGenerator() \
                    .parameters(self.SET_USER_FTA_LOCAL_PATH, f"{extension}", f"{prog_id}")
                CommandExecutor().execute(command)
