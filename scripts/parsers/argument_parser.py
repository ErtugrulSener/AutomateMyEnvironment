import argparse
import os

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)
        self.args = None

    def parse(self):
        logger.info(f"Parsing command line arguments")

        self.add_argument("-l", "--log-level", required=False,
                          help='Specify the log level, possible values are: {}'.format(
                              ', '.join(logger.get_level_name_list())))
        self.add_argument("--reinstall", required=False,
                          help='If specified, will uninstall installed software for re-installation.',
                          action='store_true')
        self.add_argument("--proxy", required=False,
                          help='If specified, the proxy will be used to download software via scoop or external tools'
                               'needed via wget. Also the requests for connection tests will be tunneled through the'
                               'proxy.')

        args = self.parse_args()

        if args.log_level:
            logger.set_log_level(args.log_level)

        if args.proxy:
            os.environ['http_proxy'] = args.proxy
            os.environ['HTTP_PROXY'] = args.proxy
            os.environ['https_proxy'] = args.proxy
            os.environ['HTTPS_PROXY'] = args.proxy

        self.args = args

    def get_arguments(self):
        return self.args

    def get_argument_value(self, name):
        return getattr(self.args, name)
