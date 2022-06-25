import re
import subprocess

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

        # Remove first and last line of choco list output, to only get software names
        command = CommandGenerator() \
            .choco() \
            .list() \
            .parameters("--local") \
            .get(len(self.installed_software) > 0)

        software_list = subprocess.check_output(command, stderr=subprocess.STDOUT).splitlines()
        software_list = software_list[1:-1]

        # Fetch name out of the acquired string, looking like for example: 'python 3.9.0'
        self.installed_software = [software.decode().split(" ")[0] for software in software_list]

    def start_installing(self):
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
            .choco() \
            .install() \
            .parameters("--no-progress", "-r", "-y", software)

        if params:
            command = command.parameters("--params", ' '.join(params))

        if logger.is_debug():
            output = subprocess.run(command.get(), capture_output=True).stdout
        else:
            output = subprocess.check_output(command.get())

        output_list = output.decode().splitlines()
        is_installed = False

        for line in output_list:
            matcher = re.match("^.*Software installed to '(.*)'.*$", line)

            if matcher:
                software_path = matcher.group(1)
                is_installed = True
                break

        if not is_installed:
            logger.error(f"Failed to install {software} with output:")

            for line in output_list:
                print(line)

            exit(4)
            return

        logger.info(f"Successfully installed {software} to {software_path}!")
        self.refresh_installed_software_cache()

    def uninstall(self, software):
        logger.info(f"Uninstalling {software} for reinstallation...")

        command = CommandGenerator() \
            .choco() \
            .uninstall() \
            .parameters("-x", "-y", software) \
            .get()

        if logger.is_debug():
            subprocess.run(command)
        else:
            subprocess.check_output(command)

        logger.info(f"Uninstalled {software} successfully.")
