from os.path import splitext, basename

from scripts.logger import Logger

logger = Logger.instance()


class Configurator:
    def __init__(self, name):
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
        logger.info(f"<{self.get_name()}>: {text}")
