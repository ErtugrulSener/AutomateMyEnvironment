import os
import winreg

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton

DESKTOP_PATH = os.path.join(os.path.join(os.environ['USERPROFILE']), r'Desktop')


@Singleton
class WindowsDesktopIconConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_THIS_PC_DESKTOP_ICON: 0,
        RegistryPath.WINDOWS_USER_HOME_DIRECTORY_DESKTOP_ICON: 0,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Enabling needed desktop icons (to user home directory and this pc) in registry")

        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            RegistryManager.instance().set(registry_key, expected_value, winreg.REG_DWORD)
