import argparse
import os

from scripts.logging.logger import Logger
from scripts.singleton import Singleton


@Singleton
class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)

        self.logger = Logger.instance()
        self.args = None

    def parse(self):
        self.logger.info(f"Parsing command line arguments...")

        self.add_argument("-l", "--log-level", required=False,
                          help='Specify the log level, possible values are: {}'.format(
                              ', '.join(self.logger.get_level_name_list())))
        self.add_argument("--reinstall", required=False,
                          help='If specified, will uninstall installed software for re-installation.',
                          action='store_true')
        self.add_argument("--http-proxy", required=False,
                          help='If specified, the proxy will be used to download software via scoop or external tools'
                               'needed via wget. Also the requests for connection tests will be tunneled through the'
                               'proxy.')
        self.add_argument("--https-proxy", required=False,
                          help='Mimics usage of http-proxy for https connections.')

        args = self.parse_args()

        if args.log_level:
            self.logger.set_log_level(args.log_level)

        if args.http_proxy:
            http_proxy = args.http_proxy
            https_proxy = args.http_proxy if not args.https_proxy else args.https_proxy

            os.environ['http_proxy'] = http_proxy
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['https_proxy'] = https_proxy
            os.environ['HTTPS_PROXY'] = https_proxy

        self.args = args

    def get_arguments(self):
        return self.args

    def get_argument_value(self, name):
        return getattr(self.args, name)
