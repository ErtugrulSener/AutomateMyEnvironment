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

    WINDOWS_ENABLE_FEEDS = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Windows Feeds",
        "EnableFeeds"
    ]

    WINDOWS_HIDE_SCA_MEET_NOW = [
        r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Policies",
        "HideSCAMeetNow"
    ]

    WINDOWS_SYSINTERNALS_AUTORUNS_EULA_ACCEPTED = [
        r"HKEY_CURRENT_USER\SOFTWARE\Sysinternals\Autoruns",
        "EulaAccepted"
    ]

    WINDOWS_APP_COMPAT_FLAGS_LAYERS = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
        ""
    ]

    WINDOWS_REGISTERED_APPLICATIONS = [
        r"HKEY_CURRENT_USER\SOFTWARE\RegisteredApplications",
        ""
    ]

    WINDOWS_START_MENU_INTERNET = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}",
        ""
    ]

    WINDOWS_START_MENU_INTERNET_APPLICATION_DESCRIPTION = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities",
        "ApplicationDescription"
    ]

    WINDOWS_START_MENU_INTERNET_APPLICATION_ICON = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities",
        "ApplicationIcon"
    ]

    WINDOWS_START_MENU_INTERNET_APPLICATION_NAME = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities",
        "ApplicationName"
    ]

    WINDOWS_START_MENU_INTERNET_STARTMENU = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities\Startmenu",
        "StartMenuInternet"
    ]

    WINDOWS_START_MENU_INTERNET_FILE_ASSOCIATIONS = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities\FileAssociations",
        ""
    ]

    WINDOWS_START_MENU_INTERNET_URL_ASSOCIATIONS = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\Capabilities\URLAssociations",
        ""
    ]

    WINDOWS_START_MENU_INTERNET_DEFAULT_ICON = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\DefaultIcon",
        ""
    ]

    WINDOWS_START_MENU_INTERNET_SHELL_OPEN_COMMAND = [
        r"HKEY_CURRENT_USER\Software\Clients\StartMenuInternet\{}\shell\open\command",
        ""
    ]

    WINDOWS_CLASSES = [
        r"HKEY_CURRENT_USER\Software\Classes\{}",
        ""
    ]

    WINDOWS_APP_USER_MODEL_ID = [
        r"HKEY_CURRENT_USER\Software\Classes\{}",
        "AppUserModelId"
    ]

    WINDOWS_SPECIFIC_APP_USER_MODEL_ID = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\Application",
        "AppUserModelId"
    ]

    WINDOWS_SPECIFIC_APP_ICON = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\Application",
        "ApplicationIcon"
    ]

    WINDOWS_SPECIFIC_APP_NAME = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\Application",
        "ApplicationName"
    ]

    WINDOWS_SPECIFIC_APP_DESCRIPTION = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\Application",
        "ApplicationDescription"
    ]

    WINDOWS_SPECIFIC_APP_COMPANY = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\Application",
        "ApplicationCompany"
    ]

    WINDOWS_SPECIFIC_APP_DEFAULT_ICON = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\DefaultIcon",
        ""
    ]

    WINDOWS_SPECIFIC_APP_SHELL_OPEN_COMMAND = [
        r"HKEY_CURRENT_USER\Software\Classes\{}\shell\open\command",
        ""
    ]

    JETBRAINS_EULA_VERSION = [
        r"HKEY_CURRENT_USER\SOFTWARE\JavaSoft\Prefs\jetbrains\privacy_policy",
        "eua_accepted_version"
    ]

    JETBRAINS_COMMUNITY_EULA_VERSION = [
        r"HKEY_CURRENT_USER\SOFTWARE\JavaSoft\Prefs\jetbrains\privacy_policy",
        "euacommunity_accepted_version"
    ]

    def get_path(self, *args):
        path = self.value[0]

        if args:
            path = path.format(*args)

        return path

    def get_registry_key(self, *args):
        registry_key = self.value[1]

        if args:
            registry_key = registry_key.format(*args)

        return registry_key


@Singleton
class RegistryManager:
    def get_table(self, key, *args):
        path, registry_key = key.value if isinstance(key, RegistryPath) else RegistryPath(key).value

        if args:
            path = path.format(*args)

        return path, registry_key

    def get(self, key, *args):
        path, registry_key = self.get_table(key, *args)
        entry = self.get_entry(path, registry_key)

        if entry:
            return entry.value

    def get_entry(self, path, registry_key):
        with WinRegistry() as client:
            try:
                return client.read_entry(path, registry_key)
            except FileNotFoundError:
                return None

    def set(self, key, value, value_type=winreg.REG_SZ, *args):
        path, registry_key = self.get_table(key, *args)
        self.set_entry(path, registry_key, value, value_type)

    def set_entry(self, path, registry_key, value, value_type=winreg.REG_SZ):
        with WinRegistry() as client:
            try:
                client.read_key(path)
            except FileNotFoundError:
                logger.debug(f"Creating new path [{path}] since it didn't exist")
                client.create_key(path)

            entry = self.get_entry(path, registry_key)

            if entry and entry.value == value:
                return

            logger.info(
                f"Setting value for registry key [{colored(os.path.join(path, registry_key), 'yellow')}] to "
                f"[{colored(value, 'yellow')}]")

            client.write_entry(path, registry_key, value, value_type)

    def delete(self, key, *args):
        path, registry_key = self.get_table(key, *args)
        self.delete_entry(path, registry_key)

    def delete_entry(self, path, registry_key):
        with WinRegistry() as client:
            logger.info(f"Removing entry [{colored(os.path.join(path, registry_key), 'yellow')}]")
            client.delete_entry(path, registry_key)
