import time
from multiprocessing import Process

import subprocess_maximize

from scripts.logging.logger import Logger

logger = Logger.instance()


class ProcessManager:
    def __init__(self, executable_path, timeout=None, print_to_console=None):
        if print_to_console is None:
            print_to_console = logger.is_trace()
        else:
            print_to_console = print_to_console and logger.is_trace()

        self.executable_path = executable_path
        self.timeout = timeout
        self.print_to_console = print_to_console

    def start_task(self, hidden=False):
        subprocess_maximize.Popen([self.executable_path, "/SINGLE", "/x", r'"-MinTSA"'],
                                  show=["normal", "hidden"][hidden],
                                  priority=0)

    def start(self):
        p = Process(target=self.start_task)
        p.start()

        if self.timeout:
            time.sleep(self.timeout)

        p.kill()
        p.close()

    def start_hidden(self):
        self.start()
