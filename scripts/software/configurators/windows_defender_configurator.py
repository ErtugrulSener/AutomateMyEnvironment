import os

import requests

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton
from scripts.software.configurator_base import ConfiguratorBase
from scripts.software.configurators.windows_services_configurator import ServiceStatus
from scripts.software.configurators.windows_services_configurator import WindowsServicesConfigurator

logger = Logger.instance()


@Singleton
class WindowsDefenderConfigurator(ConfiguratorBase):
    DEFENDER_CONTROL_LOCAL_PATH = r"external\executables\defender-control"
    DEFENDER_CONTROL_API_URL = "https://api.github.com/repos/qtkite/defender-control/releases/latest"

    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_DEFENDER_DISABLE_ANTI_SPYWARE: 1,
    }

    def __init__(self):
        super().__init__(__file__)

    def is_configured_already(self):
        if WindowsServicesConfigurator.instance().get_status("WinDefend") == ServiceStatus.RUNNING:
            return False

        for registry_key, expected_value in self.EXPECTED_REGISTRY_ENTRIES.items():
            if RegistryManager.instance().get(registry_key) != expected_value:
                return False

        return True

    def configure(self):
        logger.info("Adding myself as exception, to prevent defender from removing the defender-control tools")

        command = CommandGenerator() \
            .parameters("Add-MpPreference", "-ExclusionPath", f'"{os.getcwd()}"')
        CommandExecutor(is_powershell_command=True).execute(command)

        logger.info("Checking if the needed tools need to be downloaded...")

        if not os.path.exists(self.DEFENDER_CONTROL_LOCAL_PATH):
            self.debug(f"Created {self.DEFENDER_CONTROL_LOCAL_PATH} folder")
            os.makedirs(self.DEFENDER_CONTROL_LOCAL_PATH)

        if not os.path.exists(os.path.join(self.DEFENDER_CONTROL_LOCAL_PATH, "enable-defender.exe")) or \
                not os.path.exists(os.path.join(self.DEFENDER_CONTROL_LOCAL_PATH, "disable-defender.exe")):
            response = requests.get(url=self.DEFENDER_CONTROL_API_URL).json()

            for asset in response["assets"]:
                url = asset["browser_download_url"]

                command = CommandGenerator() \
                    .wget() \
                    .parameters("--no-clobber", "-P", self.DEFENDER_CONTROL_LOCAL_PATH, url)

                CommandExecutor().execute(command)

        self.info(f"Disabling windows defender completely")

        command = CommandGenerator() \
            .parameters(os.path.join(self.DEFENDER_CONTROL_LOCAL_PATH, "disable-defender.exe"), "-s")
        CommandExecutor().execute(command)
