import logging
import os
import re
import sys
from datetime import datetime

import coloredlogs

from scripts.singleton import Singleton

# Let python log to stdout and file
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_INSTALL_LOG_PATH = "install.log"

# Format options for logger
FORMAT_STYLE_VERBOSE = "%(asctime)s  | %(threadName)s(%(thread)d) | %(funcName)s | %(levelname)s | %(message)s"
FORMAT_STYLE_FILE_HANDLER = "%(asctime)-26s | %(funcName)-33s | %(levelname)-7s | %(message)s"
FORMAT_STYLE = "%(funcName)-33s | %(levelname)-7s | %(message)s"

FORMAT_FIELD_STYLES = coloredlogs.DEFAULT_FIELD_STYLES
FORMAT_FIELD_STYLES.update({
    'threadName': {'color': 'red'},
    'thread': {'color': 'red'},
    'funcName': {'color': 'magenta'},
    'levelname': {'color': 'green'},
})


def write_log_header(log_filepath=DEFAULT_INSTALL_LOG_PATH):
    now = datetime.now()

    with open(log_filepath, "r+") as f:
        is_initial_content = f.read()

        if is_initial_content:
            f.write('\n' * 2)

        f.writelines(['=' * 80, '\n'])
        f.writelines([f'Started logging at {now.strftime("%d/%m/%Y %H:%M:%S")}', '\n' * 2])
        f.writelines([f'{"User":<34} {os.getlogin()}', '\n'])
        f.writelines([f'{"PATH":<34} {os.environ["PATH"]}', '\n'])
        f.writelines([f'{"VIRTUAL_ENV":<34} {os.environ.get("VIRTUAL_ENV", "Not in a virtual env")}', '\n'])
        f.writelines([f'{"http_proxy":<34} {os.environ.get("http_proxy", "Not set")}', '\n'])
        f.writelines([f'{"https_proxy":<34} {os.environ.get("https_proxy", "Not set")}', '\n'])
        f.writelines(['=' * 80, '\n'])


class FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, errors=None):
        super().__init__(filename, mode, encoding, delay, errors)

        self.setFormatter(logging.Formatter(FORMAT_STYLE_FILE_HANDLER))
        self.setLevel(DEFAULT_LOG_LEVEL)

    def strip_ansi_color_codes(self, record):
        message = getattr(logging.Handler, "format")(self, record)
        return re.sub(r'\x1b[^m]*m', '', message)

    def format(self, record):
        return self.strip_ansi_color_codes(record)


@Singleton
class Logger(logging.Logger):
    logging.TRACE = 5

    def __init__(self):
        logging.Logger.__init__(self, __name__, DEFAULT_LOG_LEVEL)
        logging.addLevelName(logging.TRACE, "TRACE")

        self.file_handler = None

    def install(self):
        # Use coloredlogs to get some pretty log messages
        coloredlogs.install(logger=self, level=logging.getLevelName(DEFAULT_LOG_LEVEL), fmt=FORMAT_STYLE,
                            field_styles=FORMAT_FIELD_STYLES, stream=sys.stdout)

    def add_file_handler(self, log_filepath):
        self.file_handler = FileHandler(log_filepath)
        self.addHandler(self.file_handler)

    def set_log_level(self, level):
        level = logging._checkLevel(level.upper())

        if level == self.get_level():
            return

        for handler in self.handlers:
            handler.setLevel(level)

        self.setLevel(level)
        self.info(f"Log level set to: {self.get_level_name(level)}")

    def get_level(self):
        return self.getEffectiveLevel()

    def get_level_name(self, level):
        return logging.getLevelName(level)

    @staticmethod
    def get_level_name_list():
        return logging._levelToName.values()

    def is_debug(self):
        return self.getEffectiveLevel() == logging.DEBUG

    def is_trace(self):
        return self.getEffectiveLevel() == logging.TRACE
