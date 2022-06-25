import argparse

from scripts.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)
        self.args = None

    def parse(self):
        self.add_argument("-l", "--log-level", required=False,
                          help='Specify the log level, possible values are: {}'.format(
                              ', '.join(logger.get_level_name_list())))
        self.add_argument("--reinstall", required=False,
                          help='If specified, will uninstall installed software for reinstallation.',
                          action='store_true')

        args = self.parse_args()

        if args.log_level:
            logger.set_log_level(args.log_level)

        self.args = args

    def get_arguments(self):
        return self.args

    def get_argument_value(self, name):
        return getattr(self.args, name)
