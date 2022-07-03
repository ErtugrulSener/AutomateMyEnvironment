import argparse
from enum import Enum

from winerror import ERROR_SUCCESS
from wmi import WMI

from scripts.parsers.config_parser import ConfigParser
from scripts.software.configurator import Configurator


class ServiceStartType(Enum):
    AUTO = "Auto"
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


class WindowsServicesConfigurator(Configurator):
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
        for service in self.wmi.Win32_Service(Name=service):
            match action:
                case ServiceAction.START:
                    if self.is_running(service):
                        self.info(f"{service} is already running, no need to start it")
                        return

                    if service.StartService() == ERROR_SUCCESS:
                        self.info(f"{service} was not running and is started successfully")

                case ServiceAction.STOP:
                    if not self.is_running(service):
                        self.info(f"{service} is not running, no need to stop it")
                        return

                    if service.StopService() == ERROR_SUCCESS:
                        self.info(f"{service} was running and is stopped successfully")

                case ServiceAction.RESTART:
                    if service.RestartService() == ERROR_SUCCESS:
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
            args = parser.parse_args(arguments.split(" "))
            expected_status = self.get_expected_status_for_action(ServiceAction(args.action))
            expected_start_mode = ServiceStartType(args.start_mode)

            if self.get_status(service) != expected_status:
                return False

            if self.get_start_mode(service) != expected_start_mode:
                return False

        return True

    def configure(self):
        self.info(f"Checking if there are windows services that need to be updated...")

        for service, arguments in ConfigParser.instance().items("WINDOWS-SERVICES"):
            args = parser.parse_args(arguments.split(" "))
            start_mode = ServiceStartType(args.start_mode)
            action = ServiceAction(args.action)

            # Set start type to the expected one for ex. set to auto or disable
            actual_start_mode = self.get_start_mode(service)
            expected_start_mode = ServiceStartType(start_mode)

            self.debug(
                f"Service '{service}' -> Start type was '{actual_start_mode.name}', "
                f"but should be '{expected_start_mode.name}'")
            self.debug(
                f"Setting start type to '{expected_start_mode.name}' for service '{service}' now...")
            self.configure_start_mode(service, start_mode)

            # Set status to the expected one for ex. start or stop service
            actual_status = self.get_status(service)
            expected_status = self.get_expected_status_for_action(action)

            self.debug(
                f"Service '{service}' -> Status was '{actual_status.name}', but should be '{expected_status.name}'")
            self.debug(
                f"Performing action '{action.name.lower()}' for service '{service}' now...")
            self.configure_status(service, action)
