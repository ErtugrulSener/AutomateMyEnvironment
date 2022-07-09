import os
import shutil
import winreg

from termcolor import colored

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.managers.md5_manager import MD5Manager
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class CmderConfigurator(ConfiguratorBase):
    SOFTWARE = "cmder"
    EXECUTABLE_NAME = "Cmder.exe"

    LOCAL_SETTINGS_FILE_LOCATION = rf"external/configurations/{SOFTWARE}/ConEmu.xml"
    CMDER_SETTINGS_FILE_LOCATION = rf"vendor\conemu-maximus5\ConEmu.xml"

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

        self.base_path = SoftwareManager.instance().get_base_path(self.SOFTWARE)
        self.executable_path = SoftwareManager.instance().get_path(self.SOFTWARE, self.EXECUTABLE_NAME)

        self.icon_path = os.path.join(self.base_path, rf"icons\{self.SOFTWARE}.ico")
        self.local_settings_path = os.path.join(os.getcwd(), self.LOCAL_SETTINGS_FILE_LOCATION)
        self.cmder_settings_path = os.path.join(self.base_path, self.CMDER_SETTINGS_FILE_LOCATION)

    def check_if_configured_already(self, *args):
        for arg in args:
            if not RegistryManager.instance().get(arg, self.SOFTWARE):
                return False

        return True

    def has_right_settings(self):
        local_settings = ''.join(open(self.local_settings_path, "r", encoding="utf-8").readlines()[4:])

        if not os.path.exists(self.cmder_settings_path):
            return False

        cmder_settings = ''.join(open(self.cmder_settings_path, "r", encoding="utf-8").readlines()[4:])
        return MD5Manager.instance().hash(local_settings) == MD5Manager.instance().hash(cmder_settings)

    def is_configured_already(self):
        registry_key_list = self.LEFT_PANEL_KEYS + self.RIGHT_PANEL_KEYS

        if not self.check_if_configured_already(*registry_key_list):
            return False

        if not self.has_right_settings():
            return False

        return True

    def create_panel_entries(self, key, key_icon, key_command):
        RegistryManager.instance().set(key, f"{self.SOFTWARE} hier öffnen", winreg.REG_SZ, self.SOFTWARE)
        RegistryManager.instance().set(key_icon, f"{self.icon_path},0", winreg.REG_SZ, self.SOFTWARE)
        RegistryManager.instance().set(key_command, f'"{self.executable_path}" "%V"', winreg.REG_SZ,
                                       self.SOFTWARE)

    def configure(self):
        if not self.check_if_configured_already(*self.LEFT_PANEL_KEYS):
            self.info("Checking registry entries for left panel")
            self.create_panel_entries(*self.LEFT_PANEL_KEYS)

        if not self.check_if_configured_already(*self.RIGHT_PANEL_KEYS):
            self.info("Checking registry entries for right panel")
            self.create_panel_entries(*self.RIGHT_PANEL_KEYS)

        if not self.has_right_settings():
            self.info(
                f"Copying settings file "
                f"from [{colored(self.local_settings_path, 'yellow')}] "
                f"to [{colored(self.cmder_settings_path, 'yellow')}]")

            shutil.copyfile(self.local_settings_path, self.cmder_settings_path)
