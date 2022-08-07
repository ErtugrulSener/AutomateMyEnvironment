import os
import winreg

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
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Setting default configurations for putty (profiles)")

        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            RegistryManager.instance().set(registry_key, expected_value, winreg.REG_SZ)
