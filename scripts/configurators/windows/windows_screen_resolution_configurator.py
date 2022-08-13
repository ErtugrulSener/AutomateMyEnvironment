from collections import defaultdict

import win32api
from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import ExecutablePaths
from scripts.singleton import Singleton


@Singleton
class WindowsScreenResolutionConfigurator(ConfiguratorBase):
    def __init__(self):
        super().__init__(__file__)

        self.device_modes = defaultdict(list)

        self.load_device_modes()

    def get_device_names(self):
        monitors = win32api.EnumDisplayMonitors()
        device_names = []

        for monitor in monitors:
            device_names.append(win32api.GetMonitorInfo(monitor[0])['Device'])

        return device_names

    def load_device_modes(self):
        for device_name in self.get_device_names():
            command = CommandGenerator() \
                .parameters(ExecutablePaths.CHANGE_SCREEN_RESOLUTION.value(), "/m", f"/d={device_name}")
            output = CommandExecutor().execute(command)

            for line in output.splitlines()[1:]:
                resolution, bit_mode, refresh_rate, mode = line.lstrip().split()

                self.device_modes[device_name].append({
                    'resolution': resolution.split("x"),
                    'bit_mode': int(bit_mode.rstrip("bit")),
                    'refresh_rate': int(refresh_rate.lstrip("@").rstrip("Hz")),
                    'mode': mode,
                })

    def get_refresh_rate(self, device_name):
        return getattr(win32api.EnumDisplaySettings(device_name, -1), 'DisplayFrequency')

    def set_refresh_rate(self, device_name, refresh_rate):
        command = CommandGenerator() \
            .parameters(ExecutablePaths.CHANGE_SCREEN_RESOLUTION.value(), f"/d={device_name}", f"/f={refresh_rate}")
        CommandExecutor().execute(command)

    def get_highest_possible_refresh_rate(self, device_name):
        return max(self.device_modes[device_name], key=lambda x: x["refresh_rate"])["refresh_rate"]

    def is_configured_already(self):
        for device_name in self.device_modes.keys():
            if self.get_highest_possible_refresh_rate(device_name) != self.get_refresh_rate(device_name):
                return False

        return True

    def configure(self):
        self.info("Updating devices refresh rates to the highest possible")

        for device_name in self.device_modes.keys():
            highest_possible_refresh_rate = self.get_highest_possible_refresh_rate(device_name)
            current_refresh_rate = self.get_refresh_rate(device_name)

            if highest_possible_refresh_rate != current_refresh_rate:
                self.info(
                    f"Setting refresh rate of device [{colored(device_name, 'yellow')}] "
                    f"to [{highest_possible_refresh_rate}]")
                self.set_refresh_rate(device_name, highest_possible_refresh_rate)
