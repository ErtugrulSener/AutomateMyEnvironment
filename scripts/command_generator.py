from scripts.logger import Logger

logger = Logger.instance()


class CommandGenerator:
    def __init__(self):
        self.reset()

    def __getattr__(self, item):
        self.__setattr__(item, self)
        self.last_argument = item
        return self

    def __call__(self, *args, **kwargs):
        if not self.last_argument:
            return

        if self.last_argument != "parameters":
            self.command.append(self.last_argument)

        if args and len(args) > 0:
            for arg in args:
                self.command.append(arg)

        return self

    def reset(self):
        self.command = []
        self.last_argument = None
        return self

    def get(self, log_command=True):
        command = ' '.join(self.command)

        if log_command:
            logger.debug(f"Executing: {self.command}")

        self.reset()
        return command
