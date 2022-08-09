import os

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.configurators.windows.windows_desktop_icon_configurator import DESKTOP_PATH
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.singleton import Singleton


@Singleton
class PuttyConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.PUTTY_DEFAULT_PUBLIC_KEY_FILE: os.path.join(DESKTOP_PATH, r"keys\private.ppk"),
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            return False

        return True

    def configure(self):
        self.info("Setting default configurations for putty (profiles)")
        RegistryManager.instance().set_all(self.EXPECTED_REGISTRY_ENTRIES)
