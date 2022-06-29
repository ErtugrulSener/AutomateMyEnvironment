from enum import Enum

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


@Singleton
class RegeditManager:
    @staticmethod
    def get(key, *args):
        path, value = RegeditPath(key).value

        if args:
            path = path.format(*args)

        logger.debug(f"Reading value {value} in path {path} by key {key}")
        return path, value
