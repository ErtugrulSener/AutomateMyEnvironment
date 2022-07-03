import winreg
from enum import Enum

from winregistry import WinRegistry

from scripts.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class RegeditPath(Enum):
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


@Singleton
class RegeditManager:
    def get_table(self, key, *args):
        path, regedit_key = key.value if isinstance(key, RegeditPath) else RegeditPath(key).value

        if args:
            path = path.format(*args)

        return path, regedit_key

    def get(self, key):
        with WinRegistry() as client:
            path, regedit_key = self.get_table(key)
            return client.read_entry(path, regedit_key).value

    def set(self, key, value, value_type=winreg.REG_SZ):
        with WinRegistry() as client:
            path, regedit_key = self.get_table(key)

            if self.get(key) == value:
                return

            logger.info(f"Setting value for regedit key {regedit_key} to {value}")
            client.write_entry(path, regedit_key, value, value_type)
