import configparser

from scripts.singleton import Singleton
from scripts.logger import Logger

logger = Logger.instance()

DEFAULT_CONFIG = "config.ini"


@Singleton
class ConfigParser(configparser.ConfigParser):
    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.optionxform = str

    def parse(self):
        logger.debug(f"Parsing default configuration: {DEFAULT_CONFIG}")
        self.read(DEFAULT_CONFIG)
        logger.debug(f"Parsing default configuration was successful.")
