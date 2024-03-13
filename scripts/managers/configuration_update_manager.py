import os

if __name__ == "__main__":
    import sys
    from pathlib import Path

    parent_path = os.environ.get("HOME")

    if not parent_path:
        parent_path = Path(os.getcwd()).parent.parent.absolute()

    if parent_path not in sys.path:
        sys.path.append(parent_path)

    os.chdir(parent_path)
    sys.path.append(os.getcwd())

import time

from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.managers.software_manager import SoftwareManager
from scripts.parsers.config_parser import ConfigParser
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.parser import Parser
from scripts.singleton import Singleton
from scripts.configurators.configurator import Configurator

from scripts.configurators.windows.windows_uac_configurator import WindowsUACConfigurator
from scripts.managers.software_update_manager import NSSM_SERVICE_FOUND_EXIT_CODE, UpdaterServiceStatus

SERVICE_NAME = "ConfigurationUpdater"

LOG_FILEPATH = r"logs\configuration_updater_service.log"
STDERR_FILEPATH = r"logs\configuration_updater_service_error.log"


RETRY_INTERVAL_SECONDS = 30


@Singleton
class ConfigurationUpdateManager:
    def __init__(self):
        self.logger = Logger.instance()

    def get_service_status(self):
        command = CommandGenerator() \
            .nssm() \
            .status() \
            .parameters(SERVICE_NAME)
        output, exit_code = CommandExecutor(expected_return_codes=[3], fetch_exit_code=True).execute(command)
        output = output.replace("\0", '').rstrip('\n')
        return output, exit_code

    def service_exists(self):
        _, exit_code = self.get_service_status()
        return exit_code == NSSM_SERVICE_FOUND_EXIT_CODE

    def service_is_running(self):
        output, _ = self.get_service_status()
        service_status = UpdaterServiceStatus(output)
        return service_status in [UpdaterServiceStatus.STARTED, UpdaterServiceStatus.RUNNING]

    def register_service(self):
        self.logger.info("Registering configuration updater service now...")

        base_path = os.getcwd()
        script_path = os.path.join(base_path, r"scripts\managers\configuration_update_manager.py")
        python_executable_path = SoftwareManager.instance().get_path("python311", "python.exe")

        command = CommandGenerator() \
            .nssm() \
            .install() \
            .parameters(SERVICE_NAME) \
            .parameters(f'"{python_executable_path}"', f'"{script_path}"')

        http_proxy = os.environ.get('http_proxy')
        https_proxy = os.environ.get('https_proxy')

        if http_proxy:
            command = command.parameters(f"--http-proxy {http_proxy}")

        if https_proxy:
            command = command.parameters(f"--https-proxy {https_proxy}")

        CommandExecutor().execute(command)

        self.logger.info("Registered configuration updater started successfully!")

        self.logger.info(f"Setting app environment home to: [{colored(base_path, 'yellow')}]")
        self.set_service_parameters("AppEnvironmentExtra",
                                    f'HOME="{base_path}" USER="{os.getlogin()}" ALIAS="{os.environ["ALIAS"]}"')

        stderr_filepath = os.path.join(base_path, STDERR_FILEPATH)
        self.logger.info(f"Setting log directory for stdout / stderr to: [{colored(stderr_filepath, 'yellow')}]")

        if not os.path.exists(os.path.dirname(stderr_filepath)):
            os.makedirs(os.path.dirname(stderr_filepath))

        # self.set_service_parameters("AppStdout", stdout_filepath)
        self.set_service_parameters("AppStderr", stderr_filepath)

    def set_service_parameters(self, parameter_name, parameter_value):
        command = CommandGenerator() \
            .nssm() \
            .set() \
            .parameters(SERVICE_NAME) \
            .parameters(parameter_name, parameter_value)
        CommandExecutor().execute(command)

    def start_service(self):
        self.logger.info("Starting configuration updater service now...")

        command = CommandGenerator() \
            .nssm() \
            .start() \
            .parameters(SERVICE_NAME)
        CommandExecutor().execute(command)

        self.logger.info("Started configuration updater service successfully!")

    def check_for_services(self):
        if not self.service_exists():
            self.register_service()

        if not self.service_is_running():
            self.start_service()

    def start(self):
        self.check_for_services()

    def check_for_configuration_changes(self):
        # Check for software updates
        self.logger.info("Start checking configuration process...")
        Configurator.instance().configure(WindowsUACConfigurator)


if __name__ == "__main__":
    try:
        logger_reference = Logger.instance()
        logger_reference.install(LOG_FILEPATH)

        Parser.instance().parse(ArgumentParser)
        Parser.instance().parse(ConfigParser)

        manager = ConfigurationUpdateManager.instance()

        while True:
            manager.check_for_configuration_changes()
            time.sleep(RETRY_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        exit(0)
