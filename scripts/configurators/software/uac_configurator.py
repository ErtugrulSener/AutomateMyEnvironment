import winreg

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class UACConfigurator(ConfiguratorBase):
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.UAC_CONSENT_PROMPT_BEHAVIOR_ADMIN: 0,
        RegistryPath.UAC_ENABLE_LUA: 0,
        RegistryPath.UAC_PROMPT_ON_SECURE_DESKTOP: 0
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Setting UAC level to lowest to suppress the prompts")

        # Set UAC level to the lowest by setting the managers keys
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            RegistryManager.instance().set(registry_key, expected_value, winreg.REG_DWORD)
