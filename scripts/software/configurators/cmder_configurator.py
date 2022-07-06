import os
import winreg

from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton
from scripts.software.configurator_base import ConfiguratorBase
from scripts.software.software_installer import SoftwareInstaller

logger = Logger.instance()


@Singleton
class CmderConfigurator(ConfiguratorBase):
    EXECUTABLE_NAME = "cmder"

    LEFT_PANEL_KEYS = [
        RegistryPath.WINDOWS_LEFT_PANEL,
        RegistryPath.WINDOWS_LEFT_PANEL_ICON,
        RegistryPath.WINDOWS_LEFT_PANEL_COMMAND,
    ]

    RIGHT_PANEL_KEYS = [
        RegistryPath.WINDOWS_RIGHT_PANEL,
        RegistryPath.WINDOWS_RIGHT_PANEL_ICON,
        RegistryPath.WINDOWS_RIGHT_PANEL_COMMAND,
    ]

    def __init__(self):
        super().__init__(__file__)

    def check_if_configured_already(self, *args):
        for arg in args:
            if not RegistryManager.instance().get(arg, self.EXECUTABLE_NAME):
                return False

        return True

    def is_configured_already(self):
        registry_key_list = self.LEFT_PANEL_KEYS + self.RIGHT_PANEL_KEYS
        return self.check_if_configured_already(*registry_key_list)

    def create_panel_entries(self, key, key_icon, key_command):
        executable_path = SoftwareInstaller.instance().get_path(self.EXECUTABLE_NAME).rstrip("\r").rstrip("\n")
        path, filename = os.path.split(executable_path)
        icon_path = os.path.join(path, rf"icons\{self.EXECUTABLE_NAME}.ico")

        RegistryManager.instance().set(key, f"{self.EXECUTABLE_NAME} hier öffnen", winreg.REG_SZ, self.EXECUTABLE_NAME)
        RegistryManager.instance().set(key_icon, f"{icon_path},0", winreg.REG_SZ, self.EXECUTABLE_NAME)
        RegistryManager.instance().set(key_command, f'"{executable_path}" "%V"', winreg.REG_SZ, self.EXECUTABLE_NAME)

    def configure(self):
        if not self.check_if_configured_already(*self.LEFT_PANEL_KEYS):
            self.info("Checking registry entries for left panel")
            self.create_panel_entries(*self.LEFT_PANEL_KEYS)

        if not self.check_if_configured_already(*self.RIGHT_PANEL_KEYS):
            self.info("Checking registry entries for right panel")
            self.create_panel_entries(*self.RIGHT_PANEL_KEYS)
