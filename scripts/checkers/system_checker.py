import platform

from shutil import which
from scripts import admin
from scripts.singleton import Singleton
from scripts.logger import Logger

logger = Logger.instance()


@Singleton
class SystemChecker:
    # Required dependencies
    REQUIRED_DEPENDENCIES = [
        "choco",
    ]

    @staticmethod
    def check_for_admin_rights():
        logger.info('Checking if script was called as admin (Required)')

        if not admin.is_user_admin():
            logger.error('You need administrator privileges to run this script!')
            exit(1)

    @staticmethod
    def check_if_os_is_suitable():
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

    def check(self):
        self.check_for_admin_rights()
        self.check_if_os_is_suitable()
        self.check_for_required_dependencies()
