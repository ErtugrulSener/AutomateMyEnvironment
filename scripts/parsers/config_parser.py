import configparser

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

DEFAULT_CONFIG = "config.ini"


@Singleton
class ConfigParser(configparser.ConfigParser):
    def __init__(self):
        configparser.ConfigParser.__init__(self,
                                           interpolation=configparser.ExtendedInterpolation(),
                                           inline_comment_prefixes=";"
                                           )

        self.logger = Logger.instance()
        self.optionxform = str

    def parse(self):
        self.logger.info(f"Parsing default configuration: {DEFAULT_CONFIG}")
        self.read(DEFAULT_CONFIG)
        self.logger.info(f"Parsing default configuration was successful")
