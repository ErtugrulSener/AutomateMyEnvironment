import os
import time

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class IntelliJConfigurator(ConfiguratorBase):
    JETBRAINS_CONSENT_OPTIONS_FILEPATH = os.path.join(os.environ["APPDATA"], r"JetBrains\consentOptions/accepted")
    JETBRAINS_CONSENT_OPTIONS_SCHEMA = "rsch.send.usage.stat:{version}:{enabled}:{timestamp}"
    JETBRAINS_CONSENT_OPTIONS_VERSION = "1.1"
    JETBRAINS_EULA_VERSION = "1.4"

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        if not os.path.exists(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH):
            return False

        if RegistryManager.instance().get(RegistryPath.JETBRAINS_EULA_VERSION) != self.JETBRAINS_EULA_VERSION:
            return False

        return True

    def configure(self):
        if not os.path.exists(os.path.dirname(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH)):
            os.makedirs(os.path.dirname(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH))

        if not os.path.exists(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH):
            self.info("Disable consent to send anonymous data to Jetbrains")

            with open(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH, "w") as fw:
                fw.write(self.JETBRAINS_CONSENT_OPTIONS_SCHEMA.format(version=self.JETBRAINS_CONSENT_OPTIONS_VERSION,
                                                                      enabled=0,
                                                                      timestamp=round(time.time() * 1000)))

        if RegistryManager.instance().get(RegistryPath.JETBRAINS_EULA_VERSION) != self.JETBRAINS_EULA_VERSION:
            self.info("Accept EULA check of Jetbrains")
            RegistryManager.instance().set(RegistryPath.JETBRAINS_EULA_VERSION, self.JETBRAINS_EULA_VERSION)
