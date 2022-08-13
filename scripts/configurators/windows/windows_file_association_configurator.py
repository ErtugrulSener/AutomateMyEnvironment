from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton


@Singleton
class WindowsFileAssociationConfigurator(ConfiguratorBase):
    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for extension, prog_id in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            if FileAssociationManager.instance().get(extension) != prog_id:
                return False

        return True

    def configure(self):
        for extension, prog_id in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            if FileAssociationManager.instance().get(extension) != prog_id:
                self.info(f"Setting prog id for [{colored(extension, 'yellow')}] to [{colored(prog_id, 'yellow')}]")

                command = CommandGenerator() \
                    .parameters(self.SET_USER_FTA_LOCAL_PATH, f"{extension}", f"{prog_id}")
                CommandExecutor().execute(command)
