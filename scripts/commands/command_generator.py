from scripts.logging.logger import Logger


# noinspection PyAttributeOutsideInit
class CommandGenerator:

    def __init__(self):
        self.reset()
        self.logger = Logger.instance()

    def __getattr__(self, item):
        self.__setattr__(item, self)
        self.last_argument = item
        return self

    def __add__(self, other):
        self.command += other.command
        self.last_argument = other.last_argument
        return self

    def add_to_command(self, partial_command):
        partial_command = str(partial_command)

        if partial_command.startswith("__"):
            return

        self.command.append(partial_command)

    def __call__(self, *args, **kwargs):
        if not self.last_argument:
            return

        if self.last_argument == "pipe":
            self.add_to_command("|")
        elif self.last_argument != "parameters":
            self.add_to_command(self.last_argument)

        for arg in args:
            self.add_to_command(arg)

        self.__delattr__(self.last_argument)
        self.last_argument = ""

        return self

    def reset(self):
        self.command = []
        self.last_argument = ""
        return self

    def get(self, log_command=True):
        self.logger.debug(self.command)
        command = ' '.join(self.command)

        if log_command:
            self.logger.debug(f"Executing: {self.command}")

        self.reset()
        return command
