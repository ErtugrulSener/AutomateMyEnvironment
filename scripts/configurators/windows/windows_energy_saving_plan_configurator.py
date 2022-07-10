import re
from enum import Enum

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


class PowerConfiguration(Enum):
    BALANCED = "381b4222-f694-41f0-9685-ff5bb260df2e"
    TOP_PERFORMANCE = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    POWER_SAVING_MODE = "a1841308-3541-4fab-bc81-f71556f20b4a"


@Singleton
class WindowsEnergySavingPlanConfigurator(ConfiguratorBase):
    POWERCONFIG_SETTINGS = [
        ["SCHEME_MIN", "SUB_VIDEO", "VIDEOIDLE"],
        ["SCHEME_MIN", "SUB_SLEEP", "STANDBYIDLE"],
        ["SCHEME_MIN", "SUB_SLEEP", "HIBERNATEIDLE"],
    ]

    def __init__(self):
        super().__init__(__file__)

        self.power_configurations = {}
        self.load_power_configurations()

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

    def get_setting_value(self, *args):
        command = CommandGenerator() \
            .powercfg() \
            .parameters("/q", *args)
        output = CommandExecutor().execute(command)
        lines = output.splitlines()

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
        for query in self.POWERCONFIG_SETTINGS:
            ac_value, dc_value = self.get_setting_value(*query)

            if ac_value != 0 or dc_value != 0:
                return False

        return self.power_configurations[PowerConfiguration.TOP_PERFORMANCE]

    def configure(self):
        self.info("Setting energy saving plan to: Top performance")

        command = CommandGenerator() \
            .powercfg() \
            .parameters("/s", PowerConfiguration.TOP_PERFORMANCE.value)
        CommandExecutor().execute(command)

        self.info("Prevent monitor from being closed")

        powerconfig_monitor_settings = ["monitor-timeout-ac",
                                        "monitor-timeout-dc",
                                        "standby-timeout-ac",
                                        "standby-timeout-dc",
                                        "hibernate-timeout-ac",
                                        "hibernate-timeout-ac"]

        for monitor_setting in powerconfig_monitor_settings:
            command = CommandGenerator() \
                .powercfg() \
                .parameters("/change", monitor_setting, 0)
            CommandExecutor().execute(command)
