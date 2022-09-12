import os

SERVICE_NAME = "SoftwareUpdater"

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

import re
import time
from enum import Enum
from itertools import dropwhile

from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.constants.Enums import Color, ExecutablePaths
from scripts.logging.logger import Logger
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton

LOG_FILEPATH = r"logs\software_updater_service.log"
logger = Logger.instance()

NSSM_SERVICE_FOUND_EXIT_CODE = 0
NSSM_SERVICE_NOT_FOUND_EXIT_CODE = 3


class UpdaterServiceStatus(Enum):
    STARTED = "SERVICE_STARTED"
    RUNNING = "SERVICE_RUNNING"
    STOPPED = "SERVICE_STOPPED"
    PAUSED = "SERVICE_PAUSED"


@Singleton
class SoftwareUpdateManager:
    def __init__(self):
        self.outdated_software = []

    def refresh_scoop_buckets(self):
        command = CommandGenerator() \
            .parameters(os.path.join(os.environ.get("SCOOP"), r"shims\scoop.cmd")) \
            .update()
        CommandExecutor().execute(command)

    def refresh_outdated_software(self):
        self.outdated_software = []

        command = CommandGenerator() \
            .parameters(os.path.join(os.environ.get("SCOOP"), r"shims\scoop.cmd")) \
            .status() \
            .parameters("--global")
        lines = CommandExecutor().execute(command).splitlines()
        lines = filter(None, lines)

        # Remove every line before the printed table of outdated software
        lines = list(dropwhile(lambda l: any(character not in ["-", " "] for character in l), lines))[1:]

        for line in lines:
            if "Install failed" in line:
                continue

            matcher = re.findall(r"\b[a-zA-Z0-9._-]+\b", line)

            if matcher:
                software, version, newest_version = matcher[:3]
                self.outdated_software.append((software, version, newest_version))

    def get_service_status(self):
        command = CommandGenerator() \
            .parameters(ExecutablePaths.NON_SUCKING_SERVICE_MANAGER.value(), "status", SERVICE_NAME)
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
        logger.info("Registering software updater service now...")

        base_path = os.getcwd()
        script_path = os.path.join(base_path, r"scripts\managers\software_update_manager.py")
        python_executable_path = SoftwareManager.instance().get_path("python", "python.exe")

        command = CommandGenerator() \
            .parameters(ExecutablePaths.NON_SUCKING_SERVICE_MANAGER.value(), "install", SERVICE_NAME) \
            .parameters(f'"{python_executable_path}"', f'"{script_path}"')
        CommandExecutor().execute(command)

        logger.info("Registered updater service started successfully!")

        logger.info(f"Setting app environment home to: [{colored(base_path, 'yellow')}]")
        self.set_service_parameters("AppEnvironmentExtra", f'HOME="{base_path}"')

        log_filepath = os.path.join(base_path, LOG_FILEPATH)
        logger.info(f"Setting log directory for stdout / stderr to: [{colored(log_filepath, 'yellow')}]")

        if not os.path.exists(os.path.dirname(log_filepath)):
            os.makedirs(os.path.dirname(log_filepath))

        # self.set_service_parameters("AppStdout", log_filepath)
        # self.set_service_parameters("AppStderr", log_filepath)

    def set_service_parameters(self, parameter_name, parameter_value):
        command = CommandGenerator() \
            .parameters(ExecutablePaths.NON_SUCKING_SERVICE_MANAGER.value(), "set", SERVICE_NAME) \
            .parameters(parameter_name, parameter_value)
        CommandExecutor().execute(command)

    def start_service(self):
        logger.info("Starting software updater service now...")

        command = CommandGenerator() \
            .parameters(ExecutablePaths.NON_SUCKING_SERVICE_MANAGER.value(), "start", SERVICE_NAME)
        CommandExecutor().execute(command)

        logger.info("Started software updater service successfully!")

    def check_for_services(self):
        if not self.service_exists():
            self.register_service()

        if not self.service_is_running():
            self.start_service()

    def start(self):
        self.check_for_services()

    def check_for_scoop_updates(self):
        logger.info("Checking for newer scoop updates...")

        # Check for newer scoop version
        command = CommandGenerator() \
            .parameters(os.path.join(os.environ.get("SCOOP"), r"shims\scoop.cmd")) \
            .status() \
            .parameters("--global")
        output = CommandExecutor().execute(command)

        if "Scoop out of date." in output:
            logger.info("Updating scoop since it's out of date...")

            command = CommandGenerator() \
                .parameters(os.path.join(os.environ.get("SCOOP"), r"shims\scoop.cmd")) \
                .update()
            CommandExecutor().execute(command)

            logger.info("Successfully updated scoop")

    def check_for_updates(self):
        # Check for software updates
        logger.info("Starting update process...")
        self.refresh_scoop_buckets()
        self.refresh_outdated_software()

        if not self.outdated_software:
            logger.info("Nothing to update, skipping...")
        else:
            for name, version, newest_version in self.outdated_software:
                self.update(name, version, newest_version)

    def update_software(self, software, version, newest_version):
        logger.info(
            f"Updating {software} from version [{colored(version, Color.YELLOW.value())}] to "
            f"[{colored(newest_version, Color.YELLOW.value())}]...")

        command = CommandGenerator() \
            .parameters(os.path.join(os.environ.get("SCOOP"), r"shims\scoop.cmd")) \
            .update() \
            .parameters("--global", software)
        output = CommandExecutor().execute(command)

        if "is still running" in output:
            logger.info(f"{software} is still running. Close any instances to update, skipping for now...")
        else:
            logger.info(f"Successfully updated {software}!")

    def update(self, software, version, newest_version):
        self.update_software(software, version, newest_version)


if __name__ == "__main__":
    logger.add_file_handler(LOG_FILEPATH)
    logger.install()

    manager = SoftwareUpdateManager.instance()

    while True:
        manager.check_for_scoop_updates()
        manager.check_for_updates()
        time.sleep(60 * 60)
