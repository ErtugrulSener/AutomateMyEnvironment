from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class PyCharmConfigurator(ConfiguratorBase):
    JETBRAINS_COMMUNITY_EULA_VERSION = "1.0"

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        return RegistryManager.instance().get(
            RegistryPath.JETBRAINS_COMMUNITY_EULA_VERSION) == self.JETBRAINS_COMMUNITY_EULA_VERSION

    def configure(self):
        if RegistryManager.instance().get(
                RegistryPath.JETBRAINS_COMMUNITY_EULA_VERSION) != self.JETBRAINS_COMMUNITY_EULA_VERSION:
            self.info("Accept EULA for PyCharm by setting the registry key")
            RegistryManager.instance().set(RegistryPath.JETBRAINS_COMMUNITY_EULA_VERSION,
                                           self.JETBRAINS_COMMUNITY_EULA_VERSION)
