import os

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.configurators.windows.windows_services_configurator import ServiceStatus
from scripts.configurators.windows.windows_services_configurator import WindowsServicesConfigurator
from scripts.managers.github_file_downloader import GithubFileDownloader
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


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

        if not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES):
            return False

        return True

    def configure(self):
        self.info("Adding myself as exception, to prevent defender from removing the defender-control tools")

        command = CommandGenerator() \
            .parameters("Add-MpPreference", "-ExclusionPath", f'"{os.getcwd()}"')
        CommandExecutor(is_powershell_command=True).execute(command)

        GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL, self.DEFENDER_CONTROL_LOCAL_PATH,
                                                 "enable-defender.exe")
        GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL, self.DEFENDER_CONTROL_LOCAL_PATH,
                                                 "disable-defender.exe")

        self.info(f"Disabling windows defender completely")

        command = CommandGenerator() \
            .parameters(os.path.join(self.DEFENDER_CONTROL_LOCAL_PATH, "disable-defender.exe"), "-s")
        CommandExecutor().execute(command)
