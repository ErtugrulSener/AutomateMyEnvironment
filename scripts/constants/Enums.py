import os
from enum import Enum


class ExecutablePaths(Enum):
    SET_USER_TFA = r"set-user-fta\SetUserFTA.exe"
    SET_DEFAULT_BROWSER = r"set-default-browser\SetDefaultBrowser.exe"
    ENABLE_DEFENDER = r"defender-control\enable-defender.exe"
    DISABLE_DEFENDER = r"defender-control\disable-defender.exe"
    AUTORUNS = r"autoruns\autorunsc64.exe"
    CHANGE_SCREEN_RESOLUTION = r"change-screen-resolution\ChangeScreenResolution.exe"

    def value(self):
        filepath = self._value_
        base_path = os.path.join(os.getcwd(), r"external\executables")
        return os.path.join(base_path, filepath)


class Color(Enum):
    YELLOW = 'yellow'
    MAGENTA = 'magenta'

    def value(self):
        return self._value_
