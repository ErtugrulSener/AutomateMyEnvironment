from scripts.checkers.checker import Checker
from scripts.checkers.system_checker import SystemChecker
from scripts.logger import Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
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
    Checker.instance().register(SystemChecker)

    ConfigParser.instance().parse()
    ArgumentParser.instance().parse()
    SoftwareInstaller.instance().start_installing()

    # SoftwareConfigurator.instance().configure(CmderConfigurator)
