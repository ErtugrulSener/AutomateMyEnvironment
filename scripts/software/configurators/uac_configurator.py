import winreg

from scripts.regedit_manager import RegeditManager
from scripts.regedit_manager import RegeditPath
from scripts.software.configurator import Configurator


class UACConfigurator(Configurator):
    EXPECTED_REGEDIT_ENTRIES = {
        RegeditPath.UAC_CONSENT_PROMPT_BEHAVIOR_ADMIN: 0,
        RegeditPath.UAC_ENABLE_LUA: 0,
        RegeditPath.UAC_PROMPT_ON_SECURE_DESKTOP: 0
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for registry_key, expected_value in self.EXPECTED_REGEDIT_ENTRIES.items():
            if RegeditManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Setting UAC level to lowest to suppress the prompts")

        # Set UAC level to the lowest by setting the regedit keys
        for registry_key, expected_value in self.EXPECTED_REGEDIT_ENTRIES.items():
            RegeditManager.instance().set(registry_key, expected_value, winreg.REG_DWORD)
