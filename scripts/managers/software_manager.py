import argparse
import os
import re
from enum import Enum

import win32com.client
from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.singleton import Singleton

logger = Logger.instance()

parser = argparse.ArgumentParser()
parser.add_argument('--install-context', action='store_true')
parser.add_argument('--run-as-admin', action='store_true')
parser.add_argument('--additional_arguments')


class SoftwareInfo(Enum):
    NAME = "Name"
    DESCRIPTION = "Description"
    VERSION = "Version"
    BUCKET = "Bucket"
    WEBSITE = "Website"
    LICENSE = "License"
    UPDATED_AT = "Updated at"
    UPDATED_BY = "Updated by"
    INSTALLED = "Installed"
    BINARIES = "Binaries"
    SHORTCUTS = "Shortcuts"
    ENVIRONMENT = "Environment"
    NOTES = "Notes"


@Singleton
class SoftwareManager:
    SCOOP_APPS_SHORTCUT_PATH = os.path.join(os.environ["PROGRAMDATA"],
                                            r"Microsoft\Windows\Start Menu\Programs\Scoop Apps")

    def __init__(self):
        self.installed_software = []
        self.refresh_installed_software_cache()

    def refresh_installed_software_cache(self):
        if self.installed_software:
            logger.info("Refreshing installed software cache!")

        # Remove first and last line of output, to only get software names
        command = CommandGenerator() \
            .scoop() \
            .list()

        output = CommandExecutor().execute(
            command).splitlines()
        output = output[4:-2]

        # Fetch name out of the acquired string, looking like for example: 'python 3.9.0'
        for line in output:
            match = re.match(r"(\S+)\s+(\S+)\s+.*", line)

            if match:
                software_name = match.group(1)
                self.installed_software.append(software_name)

    def start(self):
        logger.info("Starting installation process...")

        for name, arguments in ConfigParser.instance().items("SOFTWARE_LIST"):
            args = parser.parse_args(arguments.split())
            self.install(name, args)

    def is_installed(self, software):
        return software in self.installed_software

    def get_path(self, software, executable_name):
        return os.path.join(self.get_base_path(software), executable_name)

    def get_persist_path(self, software):
        return os.path.join(os.environ["SCOOP_GLOBAL"], rf"persist\{software.lower()}")

    def get_base_path(self, software):
        return os.path.join(os.environ["SCOOP_GLOBAL"], rf"apps\{software.lower()}\current")

    def install_software(self, software, args):
        if self.is_installed(software):
            if ArgumentParser.instance().get_argument_value("reinstall"):
                self.uninstall(software)
            else:
                logger.info(f"Skipping {software} since it is installed already.")
                return

        logger.info(f"Installing {software}...")

        command = CommandGenerator() \
            .scoop() \
            .install() \
            .parameters("--global", software)

        if args.additional_arguments:
            command = command.parameters(*args.additional_arguments.split())

        output = CommandExecutor().execute(command)

        logger.info(f"Successfully installed {software}!")
        self.refresh_installed_software_cache()

        if args.install_context:
            self.install_context(software, args, output)

        if args.run_as_admin:
            self.add_run_as_admin_flag(software)

    def install(self, software, args):
        self.install_software(software, args)

    def install_context(self, software, args, output):
        logger.info(f"Installing context for {software}...")

        matcher = re.findall(r'^Add.*as a context menu option by running:.*(\r\n|\r|\n)?(".*.reg")$', output,
                             re.MULTILINE)

        for match in matcher:
            _, install_context_reg_filepath = match

            command = CommandGenerator() \
                .regedit() \
                .parameters("/s", install_context_reg_filepath)

            CommandExecutor().execute(command)

    def add_run_as_admin_flag(self, software):
        logger.info(rf"Adding '{colored('Run as Admin', 'yellow')}' flag to {colored(software, 'yellow')}")
        shortcuts = self.get_info(software, SoftwareInfo.SHORTCUTS)

        for shortcut in shortcuts.split(" | "):
            shortcut_filepath = os.path.join(self.SCOOP_APPS_SHORTCUT_PATH, f"{shortcut}.lnk")

            if os.path.exists(shortcut_filepath):
                logger.debug(f"Found shortcut at path [{shortcut_filepath}], adding 'Run as Admin' "
                             f"flag for it now...")

                shell = win32com.client.Dispatch("WScript.Shell")
                target_of_shortcut_filepath = shell.CreateShortCut(shortcut_filepath).Targetpath

                RegistryManager.instance().set_entry(RegistryPath.WINDOWS_APP_COMPAT_FLAGS_LAYERS.value[0],
                                                     target_of_shortcut_filepath,
                                                     "~ RUNASADMIN")

    def get_info(self, software, software_info):
        command = CommandGenerator() \
            .scoop() \
            .info() \
            .parameters(software)
        output = CommandExecutor().execute(command)

        for line in output.splitlines():
            if line.startswith(software_info.value):
                return line.split(": ")[1]

    @staticmethod
    def uninstall(software):
        logger.info(f"Uninstalling {software} for re-installation...")

        command = CommandGenerator() \
            .scoop() \
            .uninstall() \
            .parameters("--global", software)
        CommandExecutor().execute(command)

        logger.info(f"Uninstalled {software} successfully.")
