import winreg
from enum import Enum

from winregistry import WinRegistry

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class RegistryPath(Enum):
    PROGRAM_FILES_PATH = [
        r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        "ProgramFiles"
    ]

    DEFAULT_INSTALLATION_PATH = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion",
        "ProgramFilesDir"
    ]

    DEFAULT_INSTALLATION_PATH_x86 = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion",
        "ProgramFilesDir (x86)"
    ]

    DEFAULT_UNINSTALLATION_PATH = [
        r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{}",
        "InstallLocation"
    ]

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
                logger.debug(f"Creating new path [{path}] since it didn't exist")
                client.create_key(path)

            if not registry_key:
                logger.info(f"Setting default value for path [{path}] to [{value}]")
            else:
                logger.info(f"Setting value for registry key [{registry_key}] to [{value}]")

            client.write_entry(path, registry_key, value, value_type)
