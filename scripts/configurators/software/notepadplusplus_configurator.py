import os
import zipfile
from itertools import chain

from termcolor import colored

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.github_file_downloader import GithubFileDownloader
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton


@Singleton
class NotepadPlusPlusConfigurator(ConfiguratorBase):
    PLUGIN_LIST = [
        ["ComparePlugin", "ComparePlugin_.*_X64.zip",
         "https://api.github.com/repos/pnedev/compare-plugin/releases/latest"],
    ]

    SOFTWARE = "notepadplusplus"
    NOTEPADPLUSPLUS_LOCAL_PATH = r"external\plugins\notepadplusplus"
    NOTEPADPLUSPLUS_API_URL = "https://api.github.com/repos/pnedev/compare-plugin/releases/latest"

    def __init__(self):
        super().__init__(__file__)

        self.base_path = SoftwareManager.instance().get_base_path(self.SOFTWARE)
        self.plugins_path = os.path.join(self.base_path, "plugins")

    def is_configured_already(self):
        return all(self.is_plugin_installed(plugin_name) for plugin_name, _, _ in self.PLUGIN_LIST)

    def is_plugin_installed(self, plugin_folder_name_regex):
        return os.path.exists(os.path.join(self.plugins_path, fr"{plugin_folder_name_regex}"))

    def configure(self):
        for plugin_name, plugin_asset_regex, plugin_api_url in chain(self.PLUGIN_LIST):
            filename = GithubFileDownloader.instance().download(plugin_api_url,
                                                                self.NOTEPADPLUSPLUS_LOCAL_PATH,
                                                                plugin_asset_regex)

            self.info(f"Extracting [{colored(filename, 'yellow')}] to [{colored(self.plugins_path, 'yellow')}]")

            with zipfile.ZipFile(os.path.join(self.NOTEPADPLUSPLUS_LOCAL_PATH, filename), 'r') as zip_ref:
                zip_ref.extractall(os.path.join(self.plugins_path, plugin_name))
