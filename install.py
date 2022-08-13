from scripts.checkers.checker import Checker
from scripts.checkers.secrets_checker import SecretsChecker
from scripts.checkers.system_checker import SystemChecker
from scripts.configurators.configurator import Configurator
from scripts.configurators.software.brave_configurator import BraveConfigurator
from scripts.configurators.software.cmder_configurator import CmderConfigurator
from scripts.configurators.software.git_configurator import GitConfigurator
from scripts.configurators.software.intellij_configurator import IntelliJConfigurator
from scripts.configurators.software.notepadplusplus_configurator import NotepadPlusPlusConfigurator
from scripts.configurators.software.putty_configurator import PuttyConfigurator
from scripts.configurators.software.pycharm_configurator import PyCharmConfigurator
from scripts.configurators.software.winscp_configurator import WinscpConfigurator
from scripts.configurators.windows.windows_autostart_configurator import WindowsAutostartConfigurator
from scripts.configurators.windows.windows_dark_mode_configurator import WindowsDarkModeConfigurator
from scripts.configurators.windows.windows_default_browser_configurator import WindowsDefaultBrowserConfigurator
from scripts.configurators.windows.windows_defender_configurator import WindowsDefenderConfigurator
from scripts.configurators.windows.windows_desktop_configurator import WindowsDesktopConfigurator
from scripts.configurators.windows.windows_desktop_icon_configurator import WindowsDesktopIconConfigurator
from scripts.configurators.windows.windows_energy_saving_plan_configurator import WindowsEnergySavingPlanConfigurator
from scripts.configurators.windows.windows_file_association_configurator import WindowsFileAssociationConfigurator
from scripts.configurators.windows.windows_folder_options_configurator import WindowsFolderOptionsConfigurator
from scripts.configurators.windows.windows_screen_resolution_configurator import WindowsScreenResolutionConfigurator
from scripts.configurators.windows.windows_services_configurator import WindowsServicesConfigurator
from scripts.configurators.windows.windows_ssh_credentials_configurator import WindowsSSHCredentialsConfigurator
from scripts.configurators.windows.windows_taskbar_configurator import WindowsTaskbarConfigurator
from scripts.configurators.windows.windows_uac_configurator import WindowsUACConfigurator
from scripts.logging.logger import Logger
from scripts.managers.push_notifier_manager import PushNotifierManager
from scripts.managers.software_manager import SoftwareManager
from scripts.parsers.argument_parser import ArgumentParser
from scripts.parsers.config_parser import ConfigParser
from scripts.parsers.parser import Parser

logger = Logger.instance()

"""
Exit codes:
    1 -> Missing admin rights, you need to run this script as an admin.
    2 -> The OS is not suitable, this script is only running under windows for now.
    3 -> You are missing important dependencies to run this script!
    4 -> Failed to install software.
    5 -> Tamper Protection needs to be disabled manually.
    6 -> Problem with the internet, a persistent connection is needed.
    7 -> The password given to decrypt the git-crypt symmetric key was invalid.

TODO:
    IntelliJ:
        - Load default configuration with settings for ultimate version (Like key bindings and so)
"""

if __name__ == "__main__":
    Parser.instance().parse(ArgumentParser)
    Parser.instance().parse(ConfigParser)

    Checker.instance().check(SystemChecker)
    Checker.instance().check(SecretsChecker)

    PushNotifierManager.instance().send_text(
        "1/4 - [AUTOMATION] Installing software now...")

    SoftwareManager.instance().start()

    PushNotifierManager.instance().send_text(
        "2/4 - [AUTOMATION] Configuring windows now...")

    Configurator.instance().configure(WindowsUACConfigurator)
    Configurator.instance().configure(WindowsDefenderConfigurator)
    Configurator.instance().configure(WindowsDesktopConfigurator)
    Configurator.instance().configure(WindowsServicesConfigurator)
    Configurator.instance().configure(WindowsEnergySavingPlanConfigurator)
    Configurator.instance().configure(WindowsFolderOptionsConfigurator)
    Configurator.instance().configure(WindowsDesktopIconConfigurator)
    Configurator.instance().configure(WindowsFileAssociationConfigurator)
    Configurator.instance().configure(WindowsDefaultBrowserConfigurator)
    Configurator.instance().configure(WindowsDarkModeConfigurator)
    Configurator.instance().configure(WindowsTaskbarConfigurator)
    Configurator.instance().configure(WindowsAutostartConfigurator)
    Configurator.instance().configure(WindowsScreenResolutionConfigurator)

    PushNotifierManager.instance().send_text(
        "3/4 - [AUTOMATION] Configuring software now...")

    Configurator.instance().configure(PuttyConfigurator)
    Configurator.instance().configure(BraveConfigurator)
    Configurator.instance().configure(GitConfigurator)
    Configurator.instance().configure(WindowsSSHCredentialsConfigurator)
    Configurator.instance().configure(CmderConfigurator)
    Configurator.instance().configure(NotepadPlusPlusConfigurator)
    Configurator.instance().configure(WinscpConfigurator)
    Configurator.instance().configure(IntelliJConfigurator)
    Configurator.instance().configure(PyCharmConfigurator)

    PushNotifierManager.instance().send_text(
        "4/4 - [AUTOMATION] The installation is finished successfully. Please review the results now.")
