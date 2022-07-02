import logging
import sys

import coloredlogs

from scripts.singleton import Singleton

# Let python log to stdout and file
DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_INSTALL_SCRIPT_PATH = "install.log"

# Format options for logger
FORMAT_STYLE_VERBOSE = "%(asctime)s  | %(threadName)s(%(thread)d) | %(funcName)s | %(levelname)s | %(message)s"
FORMAT_STYLE = "%(funcName)-33s | %(levelname)-7s | %(message)s"

FORMAT_FIELD_STYLES = coloredlogs.DEFAULT_FIELD_STYLES
FORMAT_FIELD_STYLES.update({
    'threadName': {'color': 'red'},
    'thread': {'color': 'red'},
    'funcName': {'color': 'magenta'},
    'levelname': {'color': 'green'},
})


@Singleton
class Logger(logging.Logger):
    def __init__(self):
        logging.Logger.__init__(self, __name__, DEFAULT_LOG_LEVEL)

        formatter = logging.Formatter(FORMAT_STYLE)

        file_handler = logging.FileHandler(DEFAULT_INSTALL_SCRIPT_PATH)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(DEFAULT_LOG_LEVEL)
        self.addHandler(file_handler)

        # Use coloredlogs to get some pretty log messages
        coloredlogs.install(logger=self, level=logging.getLevelName(DEFAULT_LOG_LEVEL), fmt=FORMAT_STYLE,
                            field_styles=FORMAT_FIELD_STYLES, stream=sys.stdout)

    def set_log_level(self, level):
        self.setLevel(level.upper())

    @staticmethod
    def get_level_name_list():
        return [name for name in logging._levelToName.values()]

    def is_debug(self):
        return self.getEffectiveLevel() == logging.DEBUG
