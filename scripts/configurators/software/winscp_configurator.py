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
        self.winscp_configuration = configparser.ConfigParser()
        self.winscp_configuration.read(self.winscp_configuration_filepath)

    def set_configuration_parameter(self, section, key, value):
        self.info(f"Setting configuration parameter in section [{colored(section, 'yellow')}] and "
                  f"key [{colored(key, 'yellow')}] to [{colored(value, 'yellow')}]")
        self.winscp_configuration.set(section, key, value)

    def save_configuration(self):
        self.info(f"Saving configuration file [{colored(self.winscp_configuration_filepath, 'yellow')}] now...")

        with open(self.winscp_configuration_filepath, "w") as f:
            self.winscp_configuration.write(f, space_around_delimiters=False)

    def is_configured_already(self):
        for section, key, value in chain(self.CONFIGURATION_PARAMETERS):
            if not self.winscp_configuration.get(section, key) == value:
                return False

        return True

    def configure(self):
        for section, key, value in chain(self.CONFIGURATION_PARAMETERS):
            self.set_configuration_parameter(section, key, value)

        self.save_configuration()
