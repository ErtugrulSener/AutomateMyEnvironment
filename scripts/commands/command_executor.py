import subprocess

from py_console import console
from winerror import ERROR_SUCCESS

from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger

logger = Logger.instance()


class CommandExecutor:
    def __init__(self,
                 execute_in_shell=True,
                 is_powershell_command=False,
                 print_to_console=None,
                 expected_return_codes=None,
                 encoding="cp850"):
        if print_to_console is None:
            print_to_console = logger.is_trace()
        else:
            print_to_console = print_to_console and logger.is_trace()

        if expected_return_codes is None:
            expected_return_codes = [ERROR_SUCCESS]
        else:
            expected_return_codes += [ERROR_SUCCESS]

        self.execute_in_shell = execute_in_shell
        self.is_powershell_command = is_powershell_command
        self.print_to_console = print_to_console
        self.expected_return_codes = expected_return_codes
        self.encoding = encoding

    def execute(self, command):
        output = ""

        if self.is_powershell_command:
            command = CommandGenerator().powershell() + command

        with subprocess.Popen(command.get(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              bufsize=1, universal_newlines=True,
                              text=True, shell=self.execute_in_shell, encoding=self.encoding) as p:
            for line in p.stdout:
                output += line

                if self.print_to_console:
                    console.info(line.rstrip())

            p.wait()

            if p.returncode not in self.expected_return_codes:
                raise subprocess.CalledProcessError(p.returncode, p.args)

        return output
