import os
import winreg

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.explorer_manager import ExplorerManager
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class WindowsTaskbarConfigurator(ConfiguratorBase):
    USER_PINNED_QUICK_LAUNCH_PATH = os.path.join(os.environ["APPDATA"],
                                                 fr"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_PEN_WORKSPACE_BUTTON_VISIBILITY: 0,
        RegistryPath.WINDOWS_TIPBAND_DESIRED_VISIBILITY: 0,
        RegistryPath.WINDOWS_PEOPLE_BAND: 0,
        RegistryPath.WINDOWS_SHOW_TASK_VIEW_BUTTON: 0,
        RegistryPath.WINDOWS_SHOW_CORTANA_BUTTON: 0,
        RegistryPath.WINDOWS_ENABLE_FEEDS: 0,
        RegistryPath.WINDOWS_HIDE_SCA_MEET_NOW: 1,
        RegistryPath.WINDOWS_ENABLE_AUTO_TRAY: 0,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        self.info("Hiding unnecessary taskbar elements like the windows ink tray icon")

        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            RegistryManager.instance().set(registry_key, expected_value, winreg.REG_DWORD)

        self.info("Clearing taskbar icons that are there by default")
        RegistryManager.instance().delete_tree(RegistryPath.WINDOWS_EXPLORER_TASKBAND)

        for file in os.listdir(self.USER_PINNED_QUICK_LAUNCH_PATH):
            os.remove(os.path.join(self.USER_PINNED_QUICK_LAUNCH_PATH, file))

        ExplorerManager.instance().restart()
