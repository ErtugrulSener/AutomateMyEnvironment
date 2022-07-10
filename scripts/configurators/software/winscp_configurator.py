import configparser
from itertools import chain

from termcolor import colored

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton


@Singleton
class WinscpConfigurator(ConfiguratorBase):
    SOFTWARE = "winscp"
    CONFIGURATION_PARAMETERS = [
        [r"Configuration\Interface", "ShowHiddenFiles", "1"]
    ]

    def __init__(self):
        super().__init__(__file__)

        self.winscp_configuration_filepath = SoftwareManager.instance().get_path(self.SOFTWARE, f"{self.SOFTWARE}.ini")
        self.winscp_configuration = None

        self.load_winscp_configuration()

    def load_winscp_configuration(self):
        self.winscp_configuration = configparser.ConfigParser(strict=False)
        self.winscp_configuration.read(self.winscp_configuration_filepath)

    def set_configuration_option(self, section, option, value):
        self.info(f"Setting option [{colored(option, 'yellow')}] in section [{colored(section, 'yellow')}] "
                  f"to [{colored(value, 'yellow')}]")

        if not self.winscp_configuration.has_section(section):
            self.info(f"Creating section [{colored(section, 'yellow')}] since it was missing")
            self.winscp_configuration.add_section(section)

        self.winscp_configuration.set(section, option, value)

    def save_configuration(self):
        self.info(f"Saving configuration file [{colored(self.winscp_configuration_filepath, 'yellow')}] now...")

        with open(self.winscp_configuration_filepath, "w") as f:
            self.winscp_configuration.write(f, space_around_delimiters=False)

    def is_configured_already(self):
        for section, key, value in chain(self.CONFIGURATION_PARAMETERS):
            if not self.winscp_configuration.get(section, key, fallback=None) == value:
                return False

        return True

    def configure(self):
        for section, key, value in chain(self.CONFIGURATION_PARAMETERS):
            self.set_configuration_option(section, key, value)

        self.save_configuration()
