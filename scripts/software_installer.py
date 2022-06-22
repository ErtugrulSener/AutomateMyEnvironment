import subprocess

from scripts.singleton import Singleton
from scripts.config_parser import ConfigParser
from scripts.logger import Logger

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

        for entry in ConfigParser.instance().items("SOFTWARE_LIST"):
            software, params = entry
            self.install(software, params)

    def is_installed(self, software):
        return software in self.installed_software

    def install(self, software, params):
        if self.is_installed(software):
            logger.info(f"Skipping {software} since it is installed already.")
            return

        logger.info(f"Installing {software}...")

        command = f"choco install -r -y {software}"

        if params:
            command += f" --params '{' '.join(params)}'"

        if logger.is_debug():
            output = subprocess.run(command)
        else:
            output = subprocess.check_output(command)

        if not self.is_installed(software):
            logger.error(f"Failed to install {software} with last output:")
            logger.error(output)
            exit(4)

        logger.info(f"Successfully installed {software}!")
        self.refresh_installed_software_cache()
