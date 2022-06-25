from enum import Enum

from scripts.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class RegeditPath(Enum):
    DEFAULT_INSTALLATION_PATH = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion",
        "ProgramFilesDir",
    ]

    DEFAULT_INSTALLATION_PATH_x86 = {
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion",
        "ProgramFilesDir (x86)",
    }


@Singleton
class RegeditManager:
    def get(self, key):
        logger.debug(f"Fetching regedit key {key}")
        return RegeditPath(key).value
