import os
import winreg
from enum import Enum

from termcolor import colored
from winregistry import WinRegistry

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class RegistryPath(Enum):
    UAC_CONSENT_PROMPT_BEHAVIOR_ADMIN = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        "ConsentPromptBehaviorAdmin"
    ]

    UAC_ENABLE_LUA = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        "EnableLUA"
    ]

    UAC_PROMPT_ON_SECURE_DESKTOP = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        "PromptOnSecureDesktop"
    ]

    WINDOWS_DEFENDER_DISABLE_ANTI_SPYWARE = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender",
        "DisableAntiSpyware"
    ]

    WINDOWS_DEFENDER_TAMPER_PROTECTION = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Defender\Features",
        "TamperProtection"
    ]

    WINDOWS_BACKGROUND_COLOR = [
        r"HKEY_CURRENT_USER\Control Panel\Colors",
        "Background"
    ]

    WINDOWS_WALLPAPER = [
        r"HKEY_CURRENT_USER\Control Panel\Desktop",
        "Background"
    ]

    WINDOWS_SEE_HIDDEN_FOLDERS_AND_FILES = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "Hidden"
    ]

    WINDOWS_HIDE_FILE_EXTENSIONS = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "HideFileExt"
    ]

    WINDOWS_THIS_PC_DESKTOP_ICON = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
        "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
    ]

    WINDOWS_USER_HOME_DIRECTORY_DESKTOP_ICON = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
        "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
    ]

    WINDOWS_LEFT_PANEL = [
        r"HKEY_CLASSES_ROOT\Directory\Background\shell\{}",
        ""
    ]

    WINDOWS_LEFT_PANEL_ICON = [
        r"HKEY_CLASSES_ROOT\Directory\Background\shell\{}",
        "Icon"
    ]

    WINDOWS_LEFT_PANEL_COMMAND = [
        r"HKEY_CLASSES_ROOT\Directory\Background\shell\{}\command",
        ""
    ]

    WINDOWS_RIGHT_PANEL = [
        r"HKEY_CLASSES_ROOT\Directory\shell\{}",
        ""
    ]

    WINDOWS_RIGHT_PANEL_ICON = [
        r"HKEY_CLASSES_ROOT\Directory\shell\{}",
        "Icon"
    ]

    WINDOWS_RIGHT_PANEL_COMMAND = [
        r"HKEY_CLASSES_ROOT\Directory\shell\{}\command",
        ""
    ]

    WINDOWS_APPS_USE_LIGHT_THEME = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "AppsUseLightTheme"
    ]

    WINDOWS_SYSTEM_USES_LIGHT_THEME = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "SystemUsesLightTheme"
    ]

    WINDOWS_PEN_WORKSPACE_BUTTON_VISIBILITY = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\PenWorkspace",
        "PenWorkspaceButtonDesiredVisibility"
    ]

    WINDOWS_TIPBAND_DESIRED_VISIBILITY = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\TabletTip\1.7",
        "TipbandDesiredVisibility"
    ]

    WINDOWS_PEOPLE_BAND = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People",
        "PeopleBand"
    ]

    WINDOWS_SHOW_TASK_VIEW_BUTTON = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "ShowTaskViewButton"
    ]

    WINDOWS_SHOW_CORTANA_BUTTON = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "ShowCortanaButton"
    ]

    WINDOWS_SHALL_FEEDS_TASKBAR_VIEW_MODE = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Feeds",
        "ShellFeedsTaskbarViewMode"
    ]


@Singleton
class RegistryManager:
    def get_table(self, key, *args):
        path, registry_key = key.value if isinstance(key, RegistryPath) else RegistryPath(key).value

        if args:
            path = path.format(*args)

        return path, registry_key

    def get(self, key, *args):
        with WinRegistry() as client:
            path, registry_key = self.get_table(key, *args)

            try:
                return client.read_entry(path, registry_key).value
            except FileNotFoundError:
                return None

    def set(self, key, value, value_type=winreg.REG_SZ, *args):
        with WinRegistry() as client:
            path, registry_key = self.get_table(key, *args)
            current_value = self.get(key, *args)

            if current_value == value:
                return

            if not current_value:
                logger.debug(f"Creating new path [{colored(path, 'yellow')}] since it didn't exist")
                client.create_key(path)

            logger.info(
                f"Setting value for registry key [{colored(os.path.join(path, registry_key), 'yellow')}] to "
                f"[{colored(value, 'yellow')}]")

            client.write_entry(path, registry_key, value, value_type)
