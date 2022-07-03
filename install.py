from scripts.checkers.checker import Checker
from scripts.checkers.system_checker import SystemChecker
from scripts.logger import Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.software.configurators.git_configurator import GitConfigurator
from scripts.software.configurators.uac_configurator import UACConfigurator
from scripts.software.configurators.windows_defender_configurator import WindowsDefenderConfigurator
from scripts.software.configurators.windows_services_configurator import WindowsServicesConfigurator
from scripts.software_configurator import SoftwareConfigurator
from scripts.software_installer import SoftwareInstaller

logger = Logger.instance()

"""
Exit codes:
    1 -> Missing admin rights, you need to run this script as an admin!
    2 -> The OS is not suitable, this script is only running under windows for now.
    3 -> You are missing important dependencies to run this script!
    4 -> Failed to install software

TODO:
    Cmder:
        - Add 'open cmder here' to context menu of windows via regedit
        - Load cmder settings

    IntelliJ:
        - Load default configuration with settings for ultimate version (Like key bindings and so)
"""


if __name__ == "__main__":
    ArgumentParser.instance().parse()

    Checker.instance().register(SystemChecker)
    ConfigParser.instance().parse()
    SoftwareInstaller.instance().start()

    SoftwareConfigurator.instance().configure(WindowsServicesConfigurator)
    SoftwareConfigurator.instance().configure(UACConfigurator)
    SoftwareConfigurator.instance().configure(WindowsDefenderConfigurator)
    SoftwareConfigurator.instance().configure(GitConfigurator)
