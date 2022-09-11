import argparse
from enum import Enum

from aenum import MultiValueEnum
from termcolor import colored
from winerror import ERROR_SUCCESS
from wmi import WMI

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.constants.Enums import Color
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton


class ServiceStartType(MultiValueEnum):
    AUTOMATIC = "Automatic", "Auto"
    MANUAL = "Manual"
    DISABLED = "Disabled"


class ServiceAction(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"


class ServiceStatus(Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"


parser = argparse.ArgumentParser()
parser.add_argument('--start-mode')
parser.add_argument('--action')


@Singleton
class WindowsServicesConfigurator(ConfiguratorBase):
    wmi = WMI()

    def __init__(self):
        super().__init__(__file__)

    def get_start_mode(self, service):
        for service in self.wmi.Win32_Service(Name=service):
            return ServiceStartType(service.StartMode)

    def configure_start_mode(self, service, start_mode):
        for service in self.wmi.Win32_Service(Name=service):
            service.ChangeStartMode(StartMode=start_mode.value)

    def get_status(self, service):
        for service in self.wmi.Win32_Service(Name=service):
            return ServiceStatus(service.State)

    def configure_status(self, service, action):
        for service_operator in self.wmi.Win32_Service(Name=service):
            match action:
                case ServiceAction.START:
                    if self.is_running(service):
                        self.info(f"{service} is already running, no need to start it")
                        return

                    if service_operator.StartService() == ERROR_SUCCESS:
                        self.info(f"{service} was not running and is started successfully")

                case ServiceAction.STOP:
                    if not self.is_running(service):
                        self.info(f"{service} is not running, no need to stop it")
                        return

                    if service_operator.StopService() == ERROR_SUCCESS:
                        self.info(f"{service} was running and is stopped successfully")

                case ServiceAction.RESTART:
                    if service_operator.RestartService() == ERROR_SUCCESS:
                        self.info(f"{service} restarted successfully")

    def is_running(self, service):
        return self.get_status(service) == ServiceStatus.RUNNING

    def get_expected_status_for_action(self, action):
        if action == ServiceAction.START:
            return ServiceStatus.RUNNING
        elif action == ServiceAction.STOP:
            return ServiceStatus.STOPPED

    def is_configured_already(self):
        for service, arguments in ConfigParser.instance().items("WINDOWS-SERVICES"):
            args = parser.parse_args(arguments.split())

            actual_start_mode = self.get_start_mode(service)
            expected_start_mode = ServiceStartType(args.start_mode)

            if actual_start_mode != expected_start_mode:
                return False

            action = ServiceAction(args.action)
            actual_status = self.get_status(service)
            expected_status = self.get_expected_status_for_action(action)

            if actual_status != expected_status:
                return False

        return True

    def configure(self):
        self.info(f"Checking if there are windows services that need to be updated...")

        for service, arguments in ConfigParser.instance().items("WINDOWS-SERVICES"):
            args = parser.parse_args(arguments.split())

            # Set start type to the expected one for ex. set to auto or disable
            actual_start_mode = self.get_start_mode(service)
            expected_start_mode = ServiceStartType(args.start_mode)

            if actual_start_mode != expected_start_mode:
                self.debug(
                    f"Service '{colored(service, Color.YELLOW.value())}' -> Start type was"
                    f"'{colored(actual_start_mode.name, Color.YELLOW.value())}', "
                    f"but should be '{colored(expected_start_mode.name, Color.YELLOW.value())}'")
                self.info(
                    f"Setting start type to '{colored(expected_start_mode.name, Color.YELLOW.value())}' for service "
                    f"'{colored(service, Color.YELLOW.value())}' now...")
                self.configure_start_mode(service, expected_start_mode)

            # Set status to the expected one for ex. start or stop service
            action = ServiceAction(args.action)
            actual_status = self.get_status(service)
            expected_status = self.get_expected_status_for_action(action)

            if actual_status != expected_status:
                self.debug(
                    f"Service '{colored(service, Color.YELLOW.value())}' -> Status was "
                    f"'{colored(actual_status.name, Color.YELLOW.value())}', but should be"
                    f"'{colored(expected_status.name, Color.YELLOW.value())}'")
                self.info(
                    f"Performing action '{colored(action.name.lower(), Color.YELLOW.value())}' for service '{colored(service, Color.YELLOW.value())}' now...")
                self.configure_status(service, action)
