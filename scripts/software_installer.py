import re
import subprocess

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.logger import Logger
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
            .list() \
            .get(len(self.installed_software) > 0)

        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, shell=True).splitlines()
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
        pass

    def install(self, software, params):
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

        CommandExecutor().get_output(command)

        logger.info(f"Successfully installed {software}!")
        self.refresh_installed_software_cache()

    @staticmethod
    def uninstall(software):
        logger.info(f"Uninstalling {software} for re-installation...")

        command = CommandGenerator() \
            .scoop() \
            .uninstall() \
            .parameters("--global", software) \
            .get()

        if logger.is_debug():
            subprocess.run(command, shell=True)
        else:
            subprocess.check_output(command, shell=True)

        logger.info(f"Uninstalled {software} successfully.")
