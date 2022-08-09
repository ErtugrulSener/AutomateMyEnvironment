from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class WindowsDarkModeConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_SYSTEM_USES_LIGHT_THEME: 0,
        RegistryPath.WINDOWS_APPS_USE_LIGHT_THEME: 0,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            return False

        return True

    def configure(self):
        self.info("Setting dark mode for apps and system")
        RegistryManager.instance().set_all(self.EXPECTED_REGISTRY_ENTRIES)
