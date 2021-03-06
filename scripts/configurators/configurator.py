from termcolor import colored

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class Configurator:
    configurators = []

    def configure(self, configurator):
        instance = configurator.instance()

        if instance not in self.configurators:
            self.configurators.append(instance)

        logger.info(f"Configuring {colored(instance.get_name().upper(), 'magenta')} now")

        if instance.is_configured_already():
            instance.skip()
            return

        instance.configure()
