from scripts.checker import Checker
from scripts.software_installer import SoftwareInstaller
from scripts.config_parser import ConfigParser
from scripts.argument_parser import ArgumentParser
from scripts.checkers.system_checker import SystemChecker
from scripts.logger import Logger
logger = Logger.instance()

"""
Exit codes:
    1 -> Missing admin rights, you need to run this script as an admin!
    2 -> The OS is not suitable, this script is only running under windows for now.
    3 -> You are missing important dependencies to run this script!
    4 -> Failed to install software
"""

if __name__ == "__main__":
    Checker.instance().register(SystemChecker)

    ConfigParser.instance().parse();
    ArgumentParser.instance().parse();
    SoftwareInstaller.instance().start_installing()

    k = input("Drücken sie eine beliebige Taste, um die Software zu terminieren.")
