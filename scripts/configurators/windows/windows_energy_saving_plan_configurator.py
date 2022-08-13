import re
from enum import Enum

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.registry_manager import RegistryManager, RegistryPath
from scripts.singleton import Singleton


class PowerConfiguration(Enum):
    BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    TOP_PERFORMANCE = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    POWER_SAVING_MODE = "a1841308-3541-4fab-bc81-f71556f20b4a"


@Singleton
class WindowsEnergySavingPlanConfigurator(ConfiguratorBase):
    POWERCONFIG_SETTINGS = [
        ("SCHEME_MIN", "SUB_VIDEO", "VIDEOIDLE", 0),
        ("SCHEME_MIN", "SUB_SLEEP", "STANDBYIDLE", 0),
        ("SCHEME_MIN", "SUB_SLEEP", "UNATTENDSLEEP", 60 * 99999),
        ("SCHEME_MIN", "SUB_SLEEP", "HIBERNATEIDLE", 0),
    ]

    def __init__(self):
        super().__init__(__file__)

        self.power_configurations = {}
        self.power_settings = {}

        self.load_power_configurations()
        self.load_power_settings()

    def load_power_configurations(self):
        command = CommandGenerator() \
            .powercfg() \
            .parameters("/l")

        output = CommandExecutor().execute(command)

        for line in output.splitlines()[3:]:
            is_active = line.endswith("*")
            match = re.match(r"^(.*:)\s([a-zA-Z\d-]+)\s+\((.*)\)([\s*]*)$", line)

            if match:
                configuration_id = match.group(2)
                self.power_configurations[PowerConfiguration(configuration_id)] = is_active

    def load_power_settings(self):
        for setting in self.POWERCONFIG_SETTINGS:
            ac_value, dc_value = self.get_setting_value(*setting)
            self.power_settings[setting[:-1]] = (ac_value, dc_value)

    def get_setting_value(self, *args):
        key = args[:-1]

        if self.power_settings.get(key):
            return self.power_settings[key]

        command = CommandGenerator() \
            .powercfg() \
            .parameters("/q", *key)
        output = CommandExecutor().execute(command)
        lines = output.splitlines()

        if len(lines) < 3:
            return 0, 0

        ac_value, dc_value = -1, -1

        ac_value_line = lines[-3]
        matcher = re.findall(r"(0[xX][\da-fA-F]+)", ac_value_line)

        if matcher:
            ac_value = int(matcher[0], 16)

        dc_value_line = lines[-2]
        matcher = re.findall(r"(0[xX][\da-fA-F]+)", dc_value_line)

        if matcher:
            dc_value = int(matcher[0], 16)

        return ac_value, dc_value

    def is_configured_already(self):
        if not self.power_configurations[PowerConfiguration.TOP_PERFORMANCE]:
            return False

        if not RegistryManager.instance().get(RegistryPath.WINDOWS_UNATTENDED_SLEEP_TIMEOUT):
            return False

        for setting in self.POWERCONFIG_SETTINGS:
            ac_value, dc_value = self.get_setting_value(*setting)
            expected_value = setting[-1]

            if ac_value != expected_value or dc_value != expected_value:
                return False

        return True

    def configure(self):
        if not self.power_configurations[PowerConfiguration.TOP_PERFORMANCE]:
            self.info("Setting energy saving plan to: Top performance")

            command = CommandGenerator() \
                .powercfg() \
                .parameters("/s", PowerConfiguration.TOP_PERFORMANCE.value)
            CommandExecutor().execute(command)

        if not RegistryManager.instance().get(RegistryPath.WINDOWS_UNATTENDED_SLEEP_TIMEOUT):
            self.info("Enabling the windows option to set the unattended sleep timeout")
            RegistryManager.instance().set(RegistryPath.WINDOWS_UNATTENDED_SLEEP_TIMEOUT, 2)

        for setting in self.POWERCONFIG_SETTINGS:
            ac_value, dc_value = self.get_setting_value(*setting)
            expected_value = setting[-1]

            if ac_value != expected_value or dc_value != expected_value:
                key = setting[:-1]
                value = setting[-1]

                command = CommandGenerator() \
                    .powercfg() \
                    .parameters("/SETACVALUEINDEX", *key, value)
                CommandExecutor().execute(command)

                command = CommandGenerator() \
                    .powercfg() \
                    .parameters("/SETDCVALUEINDEX", *key, value)
                CommandExecutor().execute(command)
