import argparse
import os
import re
from enum import Enum
from itertools import dropwhile

import win32com.client
from termcolor import colored

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.constants.Enums import Color
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
        self.outdated_software = []

        self.refresh_installed_software_cache()

    def refresh_installed_software_cache(self):
        if self.installed_software:
            logger.info("Refreshing installed software cache!")

        self.installed_software = []

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

    def load_outdated_software(self):
        command = CommandGenerator() \
            .scoop() \
            .status() \
            .parameters("--global")
        lines = CommandExecutor().execute(command).splitlines()
        lines = filter(None, lines)

        # Remove every line before the printed table of outdated software
        lines = list(dropwhile(lambda l: any(character not in ["-", " "] for character in l), lines))[1:]

        for line in lines:
            matcher = re.findall(r"\b[a-zA-Z0-9.-_]+\b", line)

            if matcher:
                software, version, newest_version = matcher[:3]
                self.outdated_software.append((software, version, newest_version))

    def pre_check(self):
        logger.info("Checking for newer scoop updates...")

        # Check for newer scoop version
        command = CommandGenerator() \
            .scoop() \
            .status() \
            .parameters("--global")
        output = CommandExecutor().execute(command)

        if "Scoop out of date." in output:
            logger.info("Updating scoop since it's out of date...")

            command = CommandGenerator() \
                .scoop() \
                .update() \
                .parameters("--global")
            CommandExecutor().execute(command)

            logger.info("Successfully updated scoop")

    def start(self):
        # Check for not installed software
        software_list = ConfigParser.instance().items("SOFTWARE_LIST")
        logger.info("Starting installation process...")

        for name, arguments in software_list:
            args = parser.parse_args(arguments.split())
            self.install(name, args)

        # Check for software updates
        logger.info("Starting update process...")
        self.load_outdated_software()

        if not self.outdated_software:
            logger.info("Nothing to update, skipping...")
        else:
            for name, version, newest_version in self.outdated_software:
                self.update(name, version, newest_version)

    def is_installed(self, software):
        return software in self.installed_software

    def get_path(self, software, executable_name):
        return os.path.join(self.get_base_path(software), executable_name)

    def get_shortcut_name(self, software):
        shortcuts = self.get_info(software, SoftwareInfo.SHORTCUTS)
        possible_shortcuts = shortcuts.split(" | ")
        return possible_shortcuts[0]

    def get_shortcut_path(self, shortcut):
        return os.path.join(self.SCOOP_APPS_SHORTCUT_PATH, f"{shortcut}.lnk")

    def get_shortcut_target_path(self, shortcut_filepath):
        shell = win32com.client.Dispatch("WScript.Shell")
        target_of_shortcut_filepath = shell.CreateShortCut(shortcut_filepath).Targetpath
        return target_of_shortcut_filepath

    def get_executable_path(self, software):
        shortcut = self.get_shortcut_name(software)
        shortcut_filepath = self.get_shortcut_path(shortcut)
        return self.get_shortcut_target_path(shortcut_filepath)

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
            self.install_context(software, output)

        if args.run_as_admin:
            self.add_run_as_admin_flag(software)

    def update_software(self, software, version, newest_version):
        logger.info(
            f"Updating {software} from version [{colored(version, Color.YELLOW.value())}] to "
            f"[{colored(newest_version, Color.YELLOW.value())}]...")

        command = CommandGenerator() \
            .scoop() \
            .update() \
            .parameters("--global", software)
        CommandExecutor().execute(command)

        logger.info(f"Successfully updated {software}!")

    def install(self, software, args):
        self.install_software(software, args)

    def update(self, software, version, newest_version):
        self.update_software(software, version, newest_version)

    def install_context(self, software, output):
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
        logger.info(
            rf"Adding '{colored('Run as Admin', Color.YELLOW.value())}' flag to {colored(software, Color.YELLOW.value())}")
        shortcuts = self.get_info(software, SoftwareInfo.SHORTCUTS)

        for shortcut in shortcuts.split(" | "):
            shortcut_filepath = self.get_shortcut_path(shortcut)

            if os.path.exists(shortcut_filepath):
                logger.debug(f"Found shortcut at path [{shortcut_filepath}], adding 'Run as Admin' "
                             f"flag for it now...")

                target_of_shortcut_filepath = self.get_shortcut_target_path(shortcut_filepath)
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
