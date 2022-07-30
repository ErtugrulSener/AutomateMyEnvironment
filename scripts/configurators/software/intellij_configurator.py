import json
import os
import shutil
import time

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton


@Singleton
class IntelliJConfigurator(ConfiguratorBase):
    SOFTWARE = "idea-ultimate"

    INTELLIJ_LICENSE_FILEPATH = "secrets/licenses/idea-ultimate"
    INTELLIJ_LICENSE_FILES = ["plugin_PCWMP.license", "idea.key"]

    JETBRAINS_CONSENT_OPTIONS_FILEPATH = os.path.join(os.environ["APPDATA"], r"JetBrains\consentOptions/accepted")
    JETBRAINS_CONSENT_OPTIONS_SCHEMA = "rsch.send.usage.stat:{version}:{enabled}:{timestamp}"
    JETBRAINS_CONSENT_OPTIONS_VERSION = "1.1"
    JETBRAINS_EULA_VERSION = "1.4"

    def __init__(self):
        super().__init__(__file__)

    def get_config_folder_path(self):  #
        base_path = os.path.join(os.environ["APPDATA"], "JetBrains")
        product_info_filepath = os.path.join(SoftwareManager.instance().get_base_path(self.SOFTWARE),
                                             r"IDE\product-info.json")

        with open(product_info_filepath, "r") as f:
            product_info_json = json.load(f)
            return os.path.join(base_path, product_info_json["dataDirectoryName"])

    def get_settings_repository_folder_path(self):
        config_folder = self.get_config_folder_path()
        return os.path.join(config_folder, "settingsRepository")

    def is_licensed(self):
        config_folder = self.get_config_folder_path()
        files_in_folder = os.listdir(config_folder)
        return all(file in files_in_folder for file in self.INTELLIJ_LICENSE_FILES)

    def has_settings_repository(self):
        return os.path.exists(self.get_settings_repository_folder_path())

    def is_configured_already(self):
        if not os.path.exists(self.JETBRAINS_CONSENT_OPTIONS_FILEPATH):
            return False

        if RegistryManager.instance().get(RegistryPath.JETBRAINS_EULA_VERSION) != self.JETBRAINS_EULA_VERSION:
            return False

        if not self.is_licensed():
            return False

        if not self.has_settings_repository():
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

        if not self.is_licensed():
            self.info("Copy license files to the correct directory for offline activation")

            for file in self.INTELLIJ_LICENSE_FILES:
                local_file = os.path.join(self.INTELLIJ_LICENSE_FILEPATH, file)
                target_file = os.path.join(self.get_config_folder_path(), file)

                if not os.path.exists(target_file):
                    shutil.copyfile(local_file, target_file)

        if not self.has_settings_repository():
            self.info("Cloning settings repository to synchronize settings")
            repository_settings_folder = self.get_settings_repository_folder_path()

            if not os.path.exists(repository_settings_folder):
                os.makedirs(repository_settings_folder)

            command = CommandGenerator() \
                .git() \
                .clone() \
                .parameters(ConfigParser.instance().get("INTELLIJ", "settings-repository"), "--quiet",
                            os.path.join(repository_settings_folder, "repository"))
            CommandExecutor().execute(command)
