import re
import winreg
from enum import Enum

from termcolor import colored
from winerror import ERROR_FILE_NOT_FOUND

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import ExecutablePaths, Color
from scripts.managers.file_association_manager import FileAssociationManager
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton


class FileExtension(Enum):
    HTM = ".htm"
    HTML = ".html"
    HTTP = "http"
    HTTPS = "https"


@Singleton
class WindowsDefaultBrowserConfigurator(ConfiguratorBase):
    SOFTWARE = "brave"
    DEFAULT_BROWSER = SOFTWARE.capitalize()
    EXECUTABLE_NAME = f"{SOFTWARE}.exe"
    DEFAULT_BROWSER_HTM = f"{SOFTWARE.capitalize()}HTM"
    PROG_ID = f"{DEFAULT_BROWSER}"

    FILE_EXTENSIONS_TO_CHECK = [value for value in FileExtension]

    def __init__(self):
        super().__init__(__file__)

        self.default_browsers = []
        self.refresh_default_browser_cache()

    def refresh_default_browser_cache(self):
        command = CommandGenerator() \
            .parameters(ExecutablePaths.SET_DEFAULT_BROWSER.to_command())
        output = CommandExecutor(expected_return_codes=[ERROR_FILE_NOT_FOUND]).execute(command)

        matcher = re.findall(r"^(HKLM|HKCU)\s(.*)\n\s{2}name: .*\n\s{2}path: .*$", output, re.MULTILINE)

        for match in matcher:
            self.default_browsers.append(match)

    def is_configured_already(self):
        for file_extension in self.FILE_EXTENSIONS_TO_CHECK:
            if FileAssociationManager.instance().get(file_extension.value) != self.DEFAULT_BROWSER_HTM:
                return False

        return True

    def find_default_type_browser_by_identifier(self, browser_identifier):
        for real_identifier_type, identifier in self.default_browsers:
            real_identifier = identifier

            if "." in identifier:
                identifier = identifier.split(".")[0]

            if identifier == browser_identifier:
                return real_identifier_type, real_identifier

    def register_default_browser(self, browser_name):
        self.info(f"Registering {colored(f'{browser_name}', Color.YELLOW.value())} as a browser")

        software_manager = SoftwareManager.instance()
        registry_manager = RegistryManager.instance()

        executable_path = software_manager.get_path(self.SOFTWARE, self.EXECUTABLE_NAME)

        # Register browser itself
        registry_manager.set_entry(RegistryPath.WINDOWS_REGISTERED_APPLICATIONS.get_path(), self.PROG_ID,
                                   rf"Software\Clients\StartMenuInternet\{self.PROG_ID}\Capabilities")

        for key in [RegistryPath.WINDOWS_START_MENU_INTERNET,
                    RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_DESCRIPTION,
                    RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_NAME]:
            registry_manager.set(key, self.DEFAULT_BROWSER, winreg.REG_SZ, self.PROG_ID)

        for key in [RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_ICON,
                    RegistryPath.WINDOWS_START_MENU_INTERNET_DEFAULT_ICON]:
            registry_manager.set(key,
                                 f"{executable_path},0",
                                 winreg.REG_SZ,
                                 self.PROG_ID)

        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_STARTMENU,
                             self.PROG_ID,
                             winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_SHELL_OPEN_COMMAND,
                             f'"{executable_path}"',
                             winreg.REG_SZ,
                             self.PROG_ID)

        # Register browser handler
        for key in [RegistryPath.WINDOWS_APP_USER_MODEL_ID,
                    RegistryPath.WINDOWS_SPECIFIC_APP_USER_MODEL_ID,
                    RegistryPath.WINDOWS_SPECIFIC_APP_NAME,
                    RegistryPath.WINDOWS_SPECIFIC_APP_COMPANY]:
            registry_manager.set(key, self.PROG_ID, winreg.REG_SZ, self.DEFAULT_BROWSER_HTM)

        for key in [RegistryPath.WINDOWS_SPECIFIC_APP_ICON,
                    RegistryPath.WINDOWS_SPECIFIC_APP_DEFAULT_ICON]:
            registry_manager.set(key, f"{executable_path},0", winreg.REG_SZ, self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_CLASSES, f"{self.DEFAULT_BROWSER} Handler", winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_DESCRIPTION, "Browse the web", winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_SHELL_OPEN_COMMAND,
                             f'"{executable_path}" --single-argument %1',
                             winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        for association in [".htm", ".html"]:
            registry_manager.set_entry(
                RegistryPath.WINDOWS_START_MENU_INTERNET_FILE_ASSOCIATIONS.get_path(self.PROG_ID),
                association,
                self.DEFAULT_BROWSER_HTM)

        for association in ["http", "https"]:
            registry_manager.set_entry(
                RegistryPath.WINDOWS_START_MENU_INTERNET_URL_ASSOCIATIONS.get_path(self.PROG_ID),
                association,
                self.DEFAULT_BROWSER_HTM)

        self.refresh_default_browser_cache()

    def set_default_browser(self, browser_name):
        self.info(f"Setting {colored(f'{browser_name}', Color.YELLOW.value())} as the default browser")
        brave_type, brave_browser_identifier = self.find_default_type_browser_by_identifier(browser_name)

        command = CommandGenerator() \
            .parameters(ExecutablePaths.SET_DEFAULT_BROWSER.to_command(), brave_type, brave_browser_identifier)
        CommandExecutor().execute(command)

    def configure(self):
        self.register_default_browser(self.DEFAULT_BROWSER)
        self.set_default_browser(self.DEFAULT_BROWSER)
