import os
import zipfile
from itertools import chain

from termcolor import colored

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import Color
from scripts.managers.github_file_downloader import GithubFileDownloader
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton


@Singleton
class NotepadPlusPlusConfigurator(ConfiguratorBase):
    PLUGIN_LIST = [
        ["ComparePlus", "ComparePlus_.*_x64.zip",
         "https://api.github.com/repos/pnedev/comparePlus/releases/latest"],
    ]

    SOFTWARE = "notepadplusplus"
    NOTEPADPLUSPLUS_LOCAL_PATH = r"external\plugins\notepadplusplus"

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
            if not self.is_plugin_installed(plugin_name):
                filename = GithubFileDownloader.instance().download(plugin_api_url,
                                                                    self.NOTEPADPLUSPLUS_LOCAL_PATH,
                                                                    plugin_asset_regex)

                self.info(
                    f"Extracting [{colored(filename, Color.YELLOW.value())}] to "
                    f"[{colored(self.plugins_path, Color.YELLOW.value())}]")

                with zipfile.ZipFile(os.path.join(self.NOTEPADPLUSPLUS_LOCAL_PATH, filename), 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(self.plugins_path, plugin_name))
