import os
import re
from enum import Enum

from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class FileExtension(Enum):
    HTM = ".htm"
    HTML = ".html"
    HTTP = "http"
    HTTPS = "https"


@Singleton
class WindowsDefaultBrowserConfigurator(ConfiguratorBase):
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
        output = CommandExecutor().execute(command)

        matcher = re.findall(r"^(HKLM|HKCU)\s(.*)\n\s{2}name: .*\n\s{2}path: .*$", output, re.MULTILINE)

        for match in matcher:
            self.default_browsers.append(match)

    def load_associated_file_extensions(self):
        command = CommandGenerator() \
            .parameters(self.SET_USER_FTA_LOCAL_PATH, "get")

        output = CommandExecutor(print_to_console=logger.is_trace()).execute(command)

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

    def configure(self):
        self.info(f"Setting {colored('Brave', 'yellow')} as the default browser")
        brave_type, brave_browser_identifier = self.find_default_type_browser_by_identifier("Brave")

        command = CommandGenerator() \
            .parameters(self.SET_DEFAULT_BROWSER_LOCAL_PATH, brave_type, brave_browser_identifier)
        CommandExecutor().execute(command)
