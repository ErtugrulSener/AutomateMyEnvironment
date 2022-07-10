import os
import winreg

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class WindowsAutostartConfigurator(ConfiguratorBase):
    AUTORUNS_LOCAL_PATH = os.path.join(os.getcwd(), r"external/executables/autoruns/autorunsc64.exe")

    def __init__(self):
        super().__init__(__file__)

        self.autostart_list = []
        self.load_autostart_list()

    def load_autostart_list(self):
        command = CommandGenerator() \
            .parameters(self.AUTORUNS_LOCAL_PATH, "-nobanner", "-m", "-a", "l", "-ct")

        output = CommandExecutor().execute(command)
        output = output.replace("\x00", "")

        lines = [line for line in output.splitlines() if line != '']

        for line in lines[1:]:
            registry_path, registry_key, is_enabled = line.split("\t")[1:4]

            if not registry_path or not registry_key:
                continue

            if is_enabled != "enabled":
                continue

            if registry_path.endswith(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"):
                self.autostart_list.append(
                    {
                        "registry_path": registry_path,
                        "registry_key": registry_key
                    }
                )

        if self.autostart_list:
            self.autostart_list = list({frozenset(item.items()): item for item in self.autostart_list}.values())

    def is_configured_already(self):
        return len(self.autostart_list) == 0

    def configure(self):
        self.info("Disabling all programs in autostart for user")

        RegistryManager.instance().set(RegistryPath.WINDOWS_SYSINTERNALS_AUTORUNS_EULA_ACCEPTED, 1,
                                       value_type=winreg.REG_DWORD)

        for entry in self.autostart_list:
            registry_path, registry_key = entry["registry_path"], entry["registry_key"]

            entry = RegistryManager.instance().get_entry(registry_path, registry_key)
            RegistryManager.instance().delete_entry(registry_path, registry_key)
            RegistryManager.instance().set_entry(os.path.join(registry_path, "AutorunsDisabled"),
                                                 registry_key,
                                                 entry.value, entry.type)
