import argparse
import winreg

from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import ExecutablePaths, Color
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton

parser = argparse.ArgumentParser()
parser.add_argument('--prog-id')
parser.add_argument('--command', nargs='+')


@Singleton
class WindowsFileAssociationConfigurator(ConfiguratorBase):
    def __init__(self):
        super().__init__(__file__)

    def get_application_name(self, prog_id):
        application_name = prog_id

        if "\\" in application_name:
            application_name = prog_id.split("\\")[-1]

        return application_name

    def is_configured_already(self):
        for extension, arguments in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            args = parser.parse_args(arguments.split())
            shell_open_command = ' '.join(args.command)

            if RegistryManager.instance().get(
                    RegistryPath.WINDOWS_ROOT_APPLICATIONS_COMMAND, args.prog_id) != shell_open_command:
                return False

            if FileAssociationManager.instance().get(extension) != args.prog_id:
                return False

        return True

    def configure(self):
        for extension, arguments in ConfigParser.instance().items("WINDOWS-FILE-ASSOCIATIONS"):
            args = parser.parse_args(arguments.split())
            shell_open_command = ' '.join(args.command)

            if RegistryManager.instance().get(RegistryPath.WINDOWS_ROOT_APPLICATIONS_COMMAND,
                                              args.prog_id) != shell_open_command:
                self.info(f"Registering file type by setting shell open command for prog id {args.prog_id}")
                RegistryManager.instance().set(RegistryPath.WINDOWS_ROOT_APPLICATIONS_COMMAND, shell_open_command,
                                               winreg.REG_SZ, args.prog_id)

            if FileAssociationManager.instance().get(extension) != args.prog_id:
                self.info(
                    f"Setting prog id for [{colored(extension, Color.YELLOW.value())}] to "
                    f"[{colored(args.prog_id, Color.YELLOW.value())}]")

                command = CommandGenerator() \
                    .parameters(ExecutablePaths.SET_USER_TFA.to_command(), f"{extension}", f"{args.prog_id}")
                CommandExecutor(run_as_admin=False).execute(command)
