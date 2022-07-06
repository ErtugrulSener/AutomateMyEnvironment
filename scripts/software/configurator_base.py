from os.path import basename
from os.path import splitext

from termcolor import colored

from scripts.logging.logger import Logger

logger = Logger.instance()


class ConfiguratorBase:
    def __init__(self, name):
        self.name = None

        self.set_name(name)

    """ The self set naming convention for new configurator files to append is: <software>_configurator.py
        This function will extract the software name from the file. """

    def set_name(self, name):
        name = splitext(basename(name))[0]
        name = name.replace("_configurator", "")

        self.name = name

    def get_name(self):
        return self.name

    def info(self, text):
        logger.info(f"<{self.name}>: {text}")

    def debug(self, text):
        logger.debug(f"<{self.name}>: {text}")

    def skip(self):
        logger.info(f"{colored(self.name.upper(), 'magenta')} is configured properly, skipping...")
