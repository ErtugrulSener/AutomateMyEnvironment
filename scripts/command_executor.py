import subprocess
import concurrent.futures

from scripts.command_generator import CommandGenerator
from scripts.logger import Logger

logger = Logger.instance()


class CommandExecutor:
    def __init__(self,
                 execute_in_shell=True,
                 is_powershell_command=False,
                 print_to_console=True):
        self.execute_in_shell = execute_in_shell
        self.is_powershell_command = is_powershell_command
        self.print_to_console = print_to_console

    def execute(self, command, timeout=5):
        if self.is_powershell_command:
            command = CommandGenerator().powershell() + command

        if logger.is_debug():
            output = ""

            with subprocess.Popen(command.get(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  bufsize=1, universal_newlines=True,
                                  text=True, shell=self.execute_in_shell, encoding="ansi") as p:
                for line in p.stdout:
                    output += line

                    if self.print_to_console:
                        print(line, end='')

                p.wait(timeout)

                if p.returncode != 0:
                    raise subprocess.CalledProcessError(p.returncode, p.args)

            return output
        else:
            return subprocess.check_output(command.get(),
                                           text=True, shell=self.execute_in_shell, stderr=subprocess.STDOUT,
                                           encoding="ansi", timeout=timeout)
