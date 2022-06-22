from scripts.singleton import Singleton


@Singleton
class Checker:
    checkers = []

    def register(self, checker):
        instance = checker.instance()

        if instance not in self.checkers:
            self.checkers.append(instance)

        instance.check()

    def get_checkers(self):
        return self.checkers
