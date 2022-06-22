from singleton import Singleton

# Required dependencies
REQUIRED_DEPENDENCIES = [
    "choco",
]

@Singleton
class Checker:
    checkers = []

    def register(self, checker):
        instance = checker()

        if instance not in self.checkers:
            self.checkers.append(instance)

        instance.check()

    def get_checkers(self):
        return self.checkers
