from scripts.checkers.checker import Checker
from scripts.checkers.system_checker import SystemChecker
from scripts.logging.logger import Logger
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.parsers.parser import Parser
from scripts.software.configurators.cmder_configurator import CmderConfigurator
from scripts.software.configurators.configurator import Configurator
from scripts.software.configurators.git_configurator import GitConfigurator
from scripts.software.configurators.ssh_credentials_configurator import SSHCredentialsConfigurator
from scripts.software.configurators.uac_configurator import UACConfigurator
from scripts.software.configurators.windows_default_browser_configurator import WindowsDefaultBrowserConfigurator
from scripts.software.configurators.windows_defender_configurator import WindowsDefenderConfigurator
from scripts.software.configurators.windows_desktop_configurator import WindowsDesktopConfigurator
from scripts.software.configurators.windows_desktop_icon_configurator import WindowsDesktopIconConfigurator
from scripts.software.configurators.windows_energy_saving_plan_configurator import WindowsEnergySavingPlanConfigurator
from scripts.software.configurators.windows_folder_options_configurator import WindowsFolderOptionsConfigurator
from scripts.software.configurators.windows_services_configurator import WindowsServicesConfigurator
from scripts.software.software_installer import SoftwareInstaller

logger = Logger.instance()

"""
Exit codes:
    1 -> Missing admin rights, you need to run this script as an admin.
    2 -> The OS is not suitable, this script is only running under windows for now.
    3 -> You are missing important dependencies to run this script!
    4 -> Failed to install software.
    5 -> Tamper Protection needs to be disabled manually.

TODO:
    Cmder:
        - Load cmder settings

    IntelliJ:
        - Load default configuration with settings for ultimate version (Like key bindings and so)
"""

if __name__ == "__main__":
    Parser.instance().parse(ArgumentParser)
    Parser.instance().parse(ConfigParser)

    Checker.instance().check(SystemChecker)
    SoftwareInstaller.instance().start()

    Configurator.instance().configure(UACConfigurator)
    Configurator.instance().configure(WindowsDefenderConfigurator)
    Configurator.instance().configure(WindowsDesktopConfigurator)
    Configurator.instance().configure(WindowsServicesConfigurator)
    Configurator.instance().configure(WindowsEnergySavingPlanConfigurator)
    Configurator.instance().configure(WindowsFolderOptionsConfigurator)
    Configurator.instance().configure(WindowsDesktopIconConfigurator)
    Configurator.instance().configure(WindowsDefaultBrowserConfigurator)

    Configurator.instance().configure(GitConfigurator)
    Configurator.instance().configure(SSHCredentialsConfigurator)
    Configurator.instance().configure(CmderConfigurator)
