import os
import re
import winreg
from enum import Enum

from termcolor import colored
from winerror import ERROR_FILE_NOT_FOUND

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton

logger = Logger.instance()


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
    SET_DEFAULT_BROWSER_LOCAL_PATH = os.path.join(os.getcwd(),
                                                  r"external/executables/set-default-browser/SetDefaultBrowser.exe")
    SET_USER_FTA_LOCAL_PATH = os.path.join(os.getcwd(), r"external/executables/set-user-fta/SetUserFTA.exe")

    def __init__(self):
        super().__init__(__file__)

        self.default_browsers = []
        self.associated_file_extensions = {}

        self.load_default_browsers()
        self.load_associated_file_extensions()

    def load_default_browsers(self):
        command = CommandGenerator() \
            .parameters(self.SET_DEFAULT_BROWSER_LOCAL_PATH)
        output = CommandExecutor(expected_return_codes=[ERROR_FILE_NOT_FOUND]).execute(command)

        matcher = re.findall(r"^(HKLM|HKCU)\s(.*)\n\s{2}name: .*\n\s{2}path: .*$", output, re.MULTILINE)

        for match in matcher:
            self.default_browsers.append(match)

    def load_associated_file_extensions(self):
        command = CommandGenerator() \
            .parameters(self.SET_USER_FTA_LOCAL_PATH, "get")

        output = CommandExecutor().execute(command)

        for line in output.splitlines():
            extension, association = line.split(", ")
            self.associated_file_extensions[extension] = association

    def is_configured_already(self):
        for file_extension in self.FILE_EXTENSIONS_TO_CHECK:
            if not self.associated_file_extensions[file_extension.value].startswith("BraveHTML"):
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
        self.info(f"Registering {colored(f'{browser_name}', 'yellow')} as a browser")

        software_manager = SoftwareManager.instance()
        registry_manager = RegistryManager.instance()

        executable_path = software_manager.get_path(self.SOFTWARE, self.EXECUTABLE_NAME)

        # Register browser itself
        registry_manager.set_entry(RegistryPath.WINDOWS_REGISTERED_APPLICATIONS.get_path(), self.PROG_ID,
                                   rf"Software\Clients\StartMenuInternet\{self.PROG_ID}\Capabilities")

        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET, self.DEFAULT_BROWSER, winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_DESCRIPTION,
                             self.DEFAULT_BROWSER, winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_ICON,
                             f"{executable_path},0",
                             winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_APPLICATION_NAME, self.DEFAULT_BROWSER,
                             winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_STARTMENU, self.PROG_ID, winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_DEFAULT_ICON,
                             f"{executable_path},0", winreg.REG_SZ,
                             self.PROG_ID)
        registry_manager.set(RegistryPath.WINDOWS_START_MENU_INTERNET_SHELL_OPEN_COMMAND,
                             f'"{executable_path}"', winreg.REG_SZ,
                             self.PROG_ID)

        # Register browser handler
        registry_manager.set(RegistryPath.WINDOWS_CLASSES, f"{self.DEFAULT_BROWSER} Handler", winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_APP_USER_MODEL_ID, self.PROG_ID, winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_USER_MODEL_ID, self.PROG_ID, winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_ICON,
                             f"{executable_path},0",
                             winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_NAME, self.PROG_ID, winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_DESCRIPTION, "Browse the web", winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_COMPANY, self.PROG_ID, winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_DEFAULT_ICON,
                             f"{executable_path},0",
                             winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        registry_manager.set(RegistryPath.WINDOWS_SPECIFIC_APP_SHELL_OPEN_COMMAND,
                             f'"{executable_path}" --single-argument "%1"',
                             winreg.REG_SZ,
                             self.DEFAULT_BROWSER_HTM)

        for association in [".htm", ".html"]:
            registry_manager.set_entry(
                RegistryPath.WINDOWS_START_MENU_INTERNET_FILE_ASSOCIATIONS.get_path().format(self.PROG_ID),
                association,
                self.DEFAULT_BROWSER_HTM)

        for association in ["http", "https"]:
            registry_manager.set_entry(
                RegistryPath.WINDOWS_START_MENU_INTERNET_URL_ASSOCIATIONS.get_path().format(self.PROG_ID),
                association,
                self.DEFAULT_BROWSER_HTM)

    def set_default_browser(self, browser_name):
        self.info(f"Setting {colored(f'{browser_name}', 'yellow')} as the default browser")
        brave_type, brave_browser_identifier = self.find_default_type_browser_by_identifier(browser_name)

        command = CommandGenerator() \
            .parameters(self.SET_DEFAULT_BROWSER_LOCAL_PATH, brave_type, brave_browser_identifier)
        CommandExecutor().execute(command)

    def configure(self):
        self.register_default_browser(self.DEFAULT_BROWSER)
        self.set_default_browser(self.DEFAULT_BROWSER)
