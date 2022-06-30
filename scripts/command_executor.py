import subprocess

from scripts.singleton import Singleton
from scripts.logger import Logger

logger = Logger.instance()


@Singleton
class CommandExecutor:
    def __init__(self):
        pass

    def get_output(self, command):
        if logger.is_debug():
            output = ""

            with subprocess.Popen(command.get(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  bufsize=1, universal_newlines=True) as p:
                for line in p.stdout:
                    print(line, end='')
                    output += line

            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)

            return output
        else:
            return subprocess.check_output(command.get(), text=True, stderr=subprocess.STDOUT)