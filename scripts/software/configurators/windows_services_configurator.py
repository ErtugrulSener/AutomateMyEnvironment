import re
from enum import Enum

from scripts.command_executor import CommandExecutor
from scripts.command_generator import CommandGenerator
from scripts.parsers.config_parser import ConfigParser
from scripts.software.configurator import Configurator

from scripts.logger import Logger

logger = Logger.instance()


class ServiceState(Enum):
    STARTED = "Started"
    STOPPED = "Stopped"
    RUNNING = "Running"


class WindowsServicesConfigurator(Configurator):
    def __init__(self):
        super().__init__(__file__)
        self.services = {}

    def load_services(self):
        command = CommandGenerator() \
            .parameters("Get-Service") \
            .pipe() \
            .ft("-auto")

        output = CommandExecutor(execute_in_shell=False,
                                 is_powershell_command=True,
                                 print_to_console=False).execute(command)

        # Skip the first two lines header
        for line in output.splitlines()[3:]:
            match = re.match(r"(\S+)\s+(\S+)\s+.*", line)

            if match:
                service_status, service_name = match.groups()
                self.services[service_name] = ServiceState(service_status)

    def get_service_status(self, service_name):
        return self.services[service_name]

    def all_set_already(self):
        for key, value in ConfigParser.instance().items("WINDOWS-SERVICES"):
            if self.get_service_status(key).name == value:
                return False

        return True

    def configure(self):
        self.load_services()

        if self.all_set_already():
            self.skip()
            return

        logger.info(f"Checking if there are windows services that need to be updated...")

        for service_name, expected_status in ConfigParser.instance().items("WINDOWS-SERVICES"):
            expected_status = ServiceState[expected_status]

            if self.get_service_status(service_name) != expected_status:
                self.info(f"Setting service '{service_name}' to status '{expected_status.name}'")

                """command = CommandGenerator() \
                    .git() \
                    .config("--global") \
                    .parameters(key, value)
                CommandExecutor().execute(command)"""
