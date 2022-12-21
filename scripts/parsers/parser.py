from scripts.singleton import Singleton


@Singleton
class Parser:
    parsers = []

    def parse(self, parser):
        instance = parser.instance()

        if instance not in self.parsers:
            self.parsers.append(instance)

        instance.parse()
