from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton


@Singleton
class ExplorerManager:
    def __init__(self):
        self.logger = Logger.instance()

    def restart(self):
        self.logger.info("Restarting windows explorer now...")

        command = CommandGenerator() \
            .parameters('-command "gps explorer | spps"')

        CommandExecutor(is_powershell_command=True).execute(command)
