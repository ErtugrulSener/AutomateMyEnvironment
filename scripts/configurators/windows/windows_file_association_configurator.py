from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import ExecutablePaths, Color
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
                self.info(
                    f"Setting prog id for [{colored(extension, Color.YELLOW.value())}] to [{colored(prog_id, Color.YELLOW.value())}]")

                command = CommandGenerator() \
                    .parameters(ExecutablePaths.SET_USER_TFA.value(), f"{extension}", f"{prog_id}")
                CommandExecutor(run_as_admin=False).execute(command)
