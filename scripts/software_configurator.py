from scripts.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SoftwareConfigurator:
    configurators = []

    def configure(self, configurator):
        instance = configurator()

        if instance not in self.configurators:
            self.configurators.append(instance)

        logger.info(f"Configuring {instance.get_name()} now")

        if instance.is_configured_already():
            instance.skip()
            return

        instance.configure()
