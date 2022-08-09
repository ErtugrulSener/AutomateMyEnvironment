from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class WindowsFolderOptionsConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_SEE_HIDDEN_FOLDERS_AND_FILES: 1,
        RegistryPath.WINDOWS_HIDE_FILE_EXTENSIONS: 0,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            return False

        return True

    def configure(self):
        self.info("Setting folder option to see hidden files and directories and known file extensions")
        RegistryManager.instance().set_all(self.EXPECTED_REGISTRY_ENTRIES)
