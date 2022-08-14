import os

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
        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            return False

        return True

    def configure(self):
        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            self.info("Enabling needed desktop icons (to user home directory and this pc) in registry")
            RegistryManager.instance().set_all(self.EXPECTED_REGISTRY_ENTRIES)
