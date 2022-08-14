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
from scripts.managers.string_manager import StringManager
from scripts.singleton import Singleton


@Singleton
class WindowsDefenderConfigurator(ConfiguratorBase):
    DEFENDER_CONTROL_API_URL = "https://api.github.com/repos/qtkite/defender-control/releases/latest"

    EXPECTED_REGISTRY_ENTRIES = {
        RegistryPath.WINDOWS_DEFENDER_DISABLE_ANTI_SPYWARE: 1,
    }

    def __init__(self):
        super().__init__(__file__)

        self.windows_defender_preferences = {}
        self.load_windows_defender_preferences()

    def load_windows_defender_preferences(self):
        command = CommandGenerator() \
            .parameters("Get-MpPreference")
        output = CommandExecutor(is_powershell_command=True).execute(command)
        lines = output.split("\n")
        lines = list(filter(None, lines))

        for line in lines:
            preference_key, preference_value = line.split(r" :")
            stripped_preference_key, stripped_preference_value = preference_key.strip(), preference_value.strip()

            if StringManager.instance().is_boolean(stripped_preference_value):
                self.windows_defender_preferences[stripped_preference_key] = StringManager.instance().str_to_bool(
                    stripped_preference_value)
            elif StringManager.instance().is_set(stripped_preference_value):
                self.windows_defender_preferences[stripped_preference_key] = StringManager.instance().str_to_set(
                    stripped_preference_value)
            elif StringManager.instance().is_int(stripped_preference_value):
                self.windows_defender_preferences[stripped_preference_key] = StringManager.instance().str_to_int(
                    stripped_preference_value)
            else:
                self.windows_defender_preferences[stripped_preference_key] = stripped_preference_value

    def defender_is_enabled(self):
        return WindowsServicesConfigurator.instance().get_status("WinDefend") == ServiceStatus.RUNNING or \
               not RegistryManager.instance().check_all(self.EXPECTED_REGISTRY_ENTRIES)

    def is_configured_already(self):
        if self.defender_is_enabled():
            return False

        return True

    def configure(self):
        path_to_be_excluded = os.getcwd()

        if path_to_be_excluded not in self.windows_defender_preferences.get("ExclusionPath", set()):
            self.info("Adding myself as exception, to prevent defender from removing the defender-control tools")

            command = CommandGenerator() \
                .parameters("Add-MpPreference", "-ExclusionPath", f'"{path_to_be_excluded}"')
            CommandExecutor(is_powershell_command=True).execute(command)

        self.info(f"Downloading defender-control executables")

        enable_defender_local_path = ExecutablePaths.ENABLE_DEFENDER.value()
        if not os.path.exists(enable_defender_local_path):
            GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL,
                                                     *os.path.split(enable_defender_local_path))

        disable_defender_local_path = ExecutablePaths.DISABLE_DEFENDER.value()
        if not os.path.exists(disable_defender_local_path):
            GithubFileDownloader.instance().download(self.DEFENDER_CONTROL_API_URL,
                                                     *os.path.split(disable_defender_local_path))

        if self.defender_is_enabled():
            self.info(f"Disabling windows defender completely")

            command = CommandGenerator() \
                .parameters(ExecutablePaths.DISABLE_DEFENDER.value(), "-s")
            CommandExecutor().execute(command)
