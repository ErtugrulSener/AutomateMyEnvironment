import re
import subprocess

from scripts.logger import Logger
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
        software_list = subprocess.check_output('choco list --local', stderr=subprocess.STDOUT).splitlines()
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
            logger.info(f"Skipping {software} since it is installed already.")
            return

        logger.info(f"Installing {software}...")

        command = f"choco install -r -y {software}.install"

        if params:
            command += f" --params '{' '.join(params)}'"

        if logger.is_debug():
            output = subprocess.run(command, capture_output=True).stdout
        else:
            output = subprocess.check_output(command)

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
