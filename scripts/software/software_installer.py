import re

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SoftwareInstaller:
    def __init__(self):
        self.installed_software = []
        self.refresh_installed_software_cache()

    def refresh_installed_software_cache(self):
        if self.installed_software:
            logger.info("Refreshing installed software cache!")

        # Remove first and last line of output, to only get software names
        command = CommandGenerator() \
            .scoop() \
            .list()

        first_time_loading = len(self.installed_software) == 0
        output = CommandExecutor(print_to_console=not first_time_loading).execute(command).splitlines()
        output = output[4:-2]

        # Fetch name out of the acquired string, looking like for example: 'python 3.9.0'
        for line in output:
            match = re.match(r"(\S+)\s+(\S+)\s+.*", line)

            if match:
                software_name = match.group(1)
                self.installed_software.append(software_name)

    def start(self):
        logger.info("Starting installation process...")

        for name, parameters in ConfigParser.instance().items("SOFTWARE_LIST"):
            self.install(name, parameters)

    def is_installed(self, software):
        return software in self.installed_software

    def get_path(self, software):
        command = CommandGenerator() \
            .scoop() \
            .which() \
            .parameters(software)

        return CommandExecutor(print_to_console=logger.is_trace()).execute(command)

    def install(self, software, parameters):
        if self.is_installed(software):
            if ArgumentParser.instance().get_argument_value("reinstall"):
                self.uninstall(software)
            else:
                logger.info(f"Skipping {software} since it is installed already.")
                return

        logger.info(f"Installing {software}...")

        command = CommandGenerator() \
            .scoop() \
            .install() \
            .parameters("--global", software)

        if parameters:
            command = command.paremters(*parameters.split())

        CommandExecutor().execute(command)

        logger.info(f"Successfully installed {software}!")
        self.refresh_installed_software_cache()

    @staticmethod
    def uninstall(software):
        logger.info(f"Uninstalling {software} for re-installation...")

        command = CommandGenerator() \
            .scoop() \
            .uninstall() \
            .parameters("--global", software)
        CommandExecutor().execute(command)

        logger.info(f"Uninstalled {software} successfully.")
