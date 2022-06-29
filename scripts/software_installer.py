import os.path
import re
import subprocess

from winregistry import WinRegistry

from scripts.command_generator import CommandGenerator
from scripts.logger import Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.regedit_manager import RegeditManager, RegeditPath
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SoftwareInstaller:
    def __init__(self):
        self.installed_software = []
        self.refresh_installed_software_cache()

    def refresh_installed_software_cache(self):
        if self.installed_software:
            logger.info("Refreshing installed software cache!")

        # Remove first and last line of choco list output, to only get software names
        command = CommandGenerator() \
            .choco() \
            .list() \
            .parameters("--local") \
            .get(len(self.installed_software) > 0)

        software_list = subprocess.check_output(command, stderr=subprocess.STDOUT).splitlines()
        software_list = software_list[1:-1]

        # Fetch name out of the acquired string, looking like for example: 'python 3.9.0'
        self.installed_software = [software.decode().split(" ")[0] for software in software_list]

    def start_installing(self):
        logger.info("Starting installation process...")

        for name, parameters in ConfigParser.instance().items("SOFTWARE_LIST"):
            self.install(name, parameters)

    def is_installed(self, software):
        return software in self.installed_software

    def get_path(self, software):
        pass

    def install(self, software, params):
        if self.is_installed(software):
            if ArgumentParser.instance().get_argument_value("reinstall"):
                self.uninstall(software)
            else:
                logger.info(f"Skipping {software} since it is installed already.")
                return

        logger.info(f"Installing {software}...")

        default_software_path = os.path.join(ConfigParser.instance().get("INSTALL", "path"), software)
        command = CommandGenerator() \
            .choco() \
            .install() \
            .parameters("--no-progress", "--limit-output", "--confirm", software)

        use_auto_installer = True
        override_program_files_directories = False

        old_program_files_directory = os.environ['PROGRAMFILES']

        if params:
            if "--install-arguments" in params:
                use_auto_installer = False

            if "--override-program-files-directories" in params:
                override_program_files_directories = True
                params = params.replace("--override-program-files-directories", "")

            if len(params) > 0:
                command = command.parameters(params)

        if override_program_files_directories:
            with WinRegistry() as client:
                path, key_name = RegeditManager.instance().get(RegeditPath.PROGRAM_FILES_PATH)
                client.write_entry(path, key_name, r"C:\Software")

        if use_auto_installer:
            command = command.parameters(f"--install-directory '{default_software_path}'")

        output = ""
        if logger.is_debug():
            with subprocess.Popen(command.get(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  bufsize=1, universal_newlines=True, shell=True) as p:
                for line in p.stdout:
                    print(line, end='')
                    output += line

            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)
        else:
            output = subprocess.check_output(command.get(), text=True, stderr=subprocess.STDOUT)

        if override_program_files_directories:
            with WinRegistry() as client:
                path, key_name = RegeditManager.instance().get(RegeditPath.PROGRAM_FILES_PATH)
                client.write_entry(path, key_name, old_program_files_directory)

        output_list = output.splitlines()
        software_path = None

        for line_index, line in enumerate(output_list):
            matcher_exact = re.match("^.*Software installed to '(.*)'.*$", line)
            matcher_default_directory = "install location is likely default." in line

            if matcher_exact:
                software_path = matcher_exact.group(1)
                break
            elif matcher_default_directory:
                # Search in default installation paths first
                for key in [RegeditPath.DEFAULT_INSTALLATION_PATH, RegeditPath.DEFAULT_INSTALLATION_PATH_x86]:
                    with WinRegistry() as client:
                        entry = client.read_entry(*RegeditManager.instance().get(key))

                        if entry and os.path.exists(os.path.join(entry.value, software)):
                            software_path = os.path.join(entry.value, software)
                            break

                # Reverse search via uninstall directory in registry
                """with WinRegistry() as client:
                    entry = client.read_entry(
                        *RegeditManager.instance().get(RegeditPath.DEFAULT_UNINSTALLATION_PATH, software))

                    if entry and os.path.exists(os.path.join(entry.value, software)):
                        software_path = os.path.join(entry.value, software)
                        is_installed = True
                        break"""

        if not software_path:
            logger.error(f"Failed to install {software} with output:")

            for line in output_list:
                print(line)

            exit(4)
            return

        logger.info(f"Successfully installed {software} to {software_path}!")
        self.refresh_installed_software_cache()

    @staticmethod
    def uninstall(software):
        logger.info(f"Uninstalling {software} for re-installation...")

        command = CommandGenerator() \
            .choco() \
            .uninstall() \
            .parameters("--remove-dependencies", "--limit-output", "--confirm", software) \
            .get()

        if logger.is_debug():
            subprocess.run(command)
        else:
            subprocess.check_output(command)

        logger.info(f"Uninstalled {software} successfully.")
