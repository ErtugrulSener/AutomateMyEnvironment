import configparser

from pushnotifier.PushNotifier import PushNotifier
from termcolor import colored

from scripts.constants.Enums import Color
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class PushNotifierManager(PushNotifier):
    CREDENTIALS_SECTION = "CREDENTIALS"
    CONFIG_FILEPATH = "secrets/credentials/push_notifier.ini"

    def __init__(self):
        self.pushnotifier_configuration = configparser.ConfigParser()
        self.pushnotifier_configuration.read(self.CONFIG_FILEPATH)

        username = self.pushnotifier_configuration.get(self.CREDENTIALS_SECTION, "username")
        password = self.pushnotifier_configuration.get(self.CREDENTIALS_SECTION, "password")
        package_name = self.pushnotifier_configuration.get(self.CREDENTIALS_SECTION, "package_name")
        api_key = self.pushnotifier_configuration.get(self.CREDENTIALS_SECTION, "api_key")

        PushNotifier.__init__(self, username, password, package_name, api_key)

    def send_text(self, text, devices=None, silent=False):
        if not devices:
            logger.info(f"Sending push notification [{colored(text, Color.YELLOW.value())}] to all devices")
        else:
            logger.info(
                f"Sending push notification [{colored(text, Color.YELLOW.value())}] to devices "
                f"[{colored(', '.join(devices), Color.YELLOW.value())}]")

        PushNotifier.send_text(self, text, devices, silent)
