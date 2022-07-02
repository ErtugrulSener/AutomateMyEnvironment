import argparse
import re
from enum import Enum

import win32serviceutil

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.logger import Logger
from scripts.parsers.config_parser import ConfigParser
from scripts.software.configurator import Configurator

logger = Logger.instance()


class ServiceStartType(Enum):
    AUTO = "auto"


class ServiceAction(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"


class ServiceStatus(Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"


parser = argparse.ArgumentParser()
parser.add_argument('--start-type')
parser.add_argument('--action')


class WindowsServicesConfigurator(Configurator):
    def __init__(self):
        super().__init__(__file__)
        self.services = {}

    def load_services(self):
        command = CommandGenerator() \
            .parameters("Get-Service") \
            .pipe() \
            .ft("-auto")

        output = CommandExecutor(is_powershell_command=True, print_to_console=False, execute_in_shell=False).execute(
            command)

        # Skip the first two lines header
        for line in output.splitlines()[3:]:
            match = re.match(r"(\S+)\s+(\S+)\s+.*", line)

            if match:
                service_status, service_name = match.groups()
                self.services[service_name] = ServiceStatus(service_status)

    def is_service_running(self, service):
        return win32serviceutil.QueryServiceStatus(service)[1] == 4

    def configure_service_status(self, service, action):
        action = action.lower()

        if action == 'stop':
            if not self.is_service_running(service):
                self.info(f"{service} is not running, no need to stop it")
                return

            win32serviceutil.StopService(service)
            self.info(f"{service} was running and is stopped successfully")
        elif action == 'start':
            if self.is_service_running(service):
                self.info(f"{service} is already running, no need to start it")
                return

            win32serviceutil.StartService(service)
            self.info(f"{service} was not running and is started successfully")
        elif action == 'restart':
            win32serviceutil.RestartService(service)
            self.info(f"{service} restarted successfully")

    def get_service_status(self, service_name):
        return self.services[service_name]

    def get_expected_status_for_action(self, action):
        if action == ServiceAction.START:
            return ServiceStatus.RUNNING
        elif action == ServiceAction.STOP:
            return ServiceStatus.STOPPED

    def all_set_already(self):
        for service_name, service_arguments in ConfigParser.instance().items("WINDOWS-SERVICES"):
            args = parser.parse_args(service_arguments.split(" "))
            action = ServiceAction(args.action)

            if self.get_expected_status_for_action(action) != self.get_service_status(service_name):
                return False

        return True

    def configure(self):
        self.load_services()

        if self.all_set_already():
            self.skip()
            return

        self.info(f"Checking if there are windows services that need to be updated...")

        for service_name, service_arguments in ConfigParser.instance().items("WINDOWS-SERVICES"):
            args = parser.parse_args(service_arguments.split(" "))

            action = ServiceAction(args.action)
            status = self.get_service_status(service_name)
            expected_status = self.get_expected_status_for_action(action)

            self.debug(
                f"Service '{service_name}' -> Status was '{status.name}', but should be '{expected_status.name}'")
            self.debug(
                f"Performing action '{action.name.lower()}' for service '{service_name}' now...")
            self.configure_service_status(service_name, action.value)

            """
            start_type = args.start_type
            if self.get_service_status(service_name) != expected_status:
                self.info(f"Setting service '{service_name}' to status '{expected_status.name}'")

                if service_info(service_name, 'status') == expected_status:
                    service_info(service_name, "start")

                command = CommandGenerator() \
                    .sc() \
                    .config() \
                    .parameters(service_name, f"start={expected_start_type}")
                CommandExecutor().execute(command)
            """
