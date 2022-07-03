import os

import requests

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.logger import Logger
from scripts.regedit_manager import RegeditManager
from scripts.regedit_manager import RegeditPath
from scripts.software.configurator import Configurator

logger = Logger.instance()


class WindowsDefenderConfigurator(Configurator):
    DEFENDER_CONTROL_LOCAL_PATH = r"external\defender-control"
    DEFENDER_CONTROL_API_URL = "https://api.github.com/repos/qtkite/defender-control/releases/latest"

    EXPECTED_REGEDIT_ENTRIES = {
        RegeditPath.WINDOWS_DEFENDER_DISABLE_ANTI_SPYWARE: 1,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        for regedit_key, expected_value in self.EXPECTED_REGEDIT_ENTRIES.items():
            if RegeditManager.instance().get(regedit_key) != expected_value:
                return False

        return True

    def configure(self):
        if not os.path.exists(self.DEFENDER_CONTROL_LOCAL_PATH):
            self.debug(f"Created {self.DEFENDER_CONTROL_LOCAL_PATH} folder")
            os.makedirs(self.DEFENDER_CONTROL_LOCAL_PATH)

        if not os.path.exists(self.DEFENDER_CONTROL_LOCAL_PATH) or not os.listdir(self.DEFENDER_CONTROL_LOCAL_PATH):
            self.info(f"Downloading newest tools to: {self.DEFENDER_CONTROL_LOCAL_PATH}")
            response = requests.get(url=self.DEFENDER_CONTROL_API_URL).json()

            for asset in response["assets"]:
                url = asset["browser_download_url"]

                command = CommandGenerator() \
                    .wget() \
                    .parameters("-P", self.DEFENDER_CONTROL_LOCAL_PATH, url)

                CommandExecutor().execute(command)

        self.info("Disabling real time monitoring service")

        command = CommandGenerator() \
            .parameters("Set-MpPreference", "-DisableRealtimeMonitoring", "1")
        CommandExecutor(is_powershell_command=True).execute(command)

        self.info(f"Disabling windows defender completely")
        command = CommandGenerator() \
            .parameters(os.path.join(self.DEFENDER_CONTROL_LOCAL_PATH, "disable-defender.exe"), "-s")
        CommandExecutor().execute(command)
