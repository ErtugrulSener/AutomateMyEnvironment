import platform
from shutil import which

import http.client as httplib

from scripts.logging.logger import Logger
from scripts.managers import admin_manager
from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SystemChecker:
    # Required dependencies
    REQUIRED_DEPENDENCIES = [
        "scoop",
    ]

    def check_for_admin_rights(self):
        logger.info('Checking if script was called as admin (Required)')

        if not admin_manager.is_user_admin():
            logger.error('You need administrator privileges to run this script!')
            exit(1)

    def check_if_os_is_suitable(self):
        logger.info('Checking if it is a suitable OS (Only windows is supported by now)')
        is_windows = any(platform.win32_ver())

        if not is_windows:
            logger.error('For now, only windows is supported!')
            exit(2)

    def check_for_required_dependencies(self):
        logger.info('Checking for dependencies...')

        found_all_dependencies = True
        for dependency in self.REQUIRED_DEPENDENCIES:
            is_installed = which(dependency) is not None
            text_to_log = f'{dependency} (Required) -> {"Found" if is_installed else "Not Found":<10}'

            if not is_installed:
                logger.error(text_to_log)
                found_all_dependencies = False
            else:
                logger.debug(text_to_log)

        if not found_all_dependencies:
            logger.error('One or more dependencies are missing, install them to proceed!')
            exit(3)

    def check_for_tamper_protection(self):
        logger.info('Checking if tamper protection feature of Windows Defender is disabled...')

        if RegistryManager.instance().get(RegistryPath.WINDOWS_DEFENDER_TAMPER_PROTECTION) != 4:
            logger.error("The tamper protection feature of Windows Defender needs to be disabled!")
            exit(5)

    def check_for_internet_connection(self):
        logger.info('Checking if user has a persistent internet connection')
        conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)

        try:
            conn.request("HEAD", "/")
        except Exception:
            logger.error("You need a persistent internet connection to run this script!")
            exit(6)
        finally:
            conn.close()

    def check(self):
        self.check_for_admin_rights()
        self.check_if_os_is_suitable()
        self.check_for_required_dependencies()
        self.check_for_tamper_protection()
        self.check_for_internet_connection()
