import os

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.configurators.windows.windows_services_configurator import ServiceStatus
from scripts.configurators.windows.windows_services_configurator import WindowsServicesConfigurator
from scripts.constants.Enums import ExecutablePaths
from scripts.managers.github_file_downloader import GithubFileDownloader
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton


@Singleton
class WindowsDefenderConfigurator(ConfiguratorBase):
    DEFENDER_CONTROL_API_URL = "https://api.github.com/repos/qtkite/defender-control/releases/latest"

    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_DEFENDER_DISABLE_ANTI_SPYWARE: 1,
    }

    def __init__(self):
        super().__init__(__file__)

    def get_exclusion_paths(self):
        command = CommandGenerator() \
            .parameters("$Preferences = Get-MpPreference; $Preferences.ExclusionPath")
        output = CommandExecutor(is_powershell_command=True).execute(command)

        if not output:
            return set()

        return set(output.splitlines())

    def defender_is_enabled(self):
        return WindowsServicesConfigurator.instance().get_status("WinDefend") == ServiceStatus.RUNNING or \
               not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES)

    def is_configured_already(self):
        if self.defender_is_enabled():
            return False

        return True

    def configure(self):
        path_to_be_excluded = os.getcwd()

        if path_to_be_excluded not in self.get_exclusion_paths():
            self.info("Adding myself as exception, to prevent defender from removing the defender-control tools")

            command = CommandGenerator() \
                .parameters("Add-MpPreference", "-ExclusionPath", f'"{path_to_be_excluded}"')
            CommandExecutor(is_powershell_command=True).execute(command)

        enable_defender_local_path = ExecutablePaths.ENABLE_DEFENDER.to_command()
        if not os.path.exists(enable_defender_local_path):
            GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL,
                                                     *os.path.split(enable_defender_local_path))

        disable_defender_local_path = ExecutablePaths.DISABLE_DEFENDER.to_command()
        if not os.path.exists(disable_defender_local_path):
            GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL,
                                                     *os.path.split(disable_defender_local_path))

        if self.defender_is_enabled():
            self.info(f"Disabling windows defender completely")

            command = CommandGenerator() \
                .parameters(ExecutablePaths.DISABLE_DEFENDER.to_command(), "-s")
            CommandExecutor().execute(command)
