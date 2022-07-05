from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class Parser:
    parsers = []

    def parse(self, parser):
        instance = parser.instance()

        if instance not in self.parsers:
            self.parsers.append(instance)

        instance.parse()
