import os.path
import platform

from termcolor import colored

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class AliasChecker:
    ALIAS_FILEPATH = r"alias"

    def check_if_alias_is_set(self):
        logger.info('Checking if alias for phone notifications is set')

        if not os.path.exists(self.ALIAS_FILEPATH):
            default_alias = f"{platform.node()}"
            alias = input(
                f"Do you wish to set an alias for phone notifications? "
                f"(default is: {colored(default_alias, 'yellow')}@{os.getlogin()}): ") or default_alias

            alias = f"{alias}@{os.getlogin()}"
            with open(self.ALIAS_FILEPATH, "w") as fw:
                fw.write(alias)

        with open(self.ALIAS_FILEPATH, "r") as f:
            os.environ["ALIAS"] = f.readline()

    def check(self):
        self.check_if_alias_is_set()
