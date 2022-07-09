import winreg

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class WindowsFolderOptionsConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_SEE_HIDDEN_FOLDERS_AND_FILES: 1,
        RegistryPath.WINDOWS_HIDE_FILE_EXTENSIONS: 0,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Setting folder option to see hidden files and directories and known file extensions")

        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            RegistryManager.instance().set(registry_key, expected_value, winreg.REG_DWORD)
