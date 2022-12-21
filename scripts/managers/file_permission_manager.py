from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton


@Singleton
class FilePermissionManager:
    def __init__(self):
        self.logger = Logger.instance()

    def remove_permission(self, filepath, username):
        self.logger.info(f"Removing permission for user {username} to file {filepath}")
        command = CommandGenerator() \
            .CACLS() \
            .parameters(f'"{filepath}"', "/e", "/r", username)
        CommandExecutor().execute(command)

    def set_read_only(self, filepath, username):
        self.logger.info(f"Setting read only permission for user {username} to file {filepath}")
        command = CommandGenerator() \
            .icacls() \
            .parameters(f'"{filepath}"', "/inheritance:r", "/grant:r", f"{username}:R")
        CommandExecutor().execute(command)

    def set_read_and_write_only(self, filepath, username):
        self.logger.info(f"Setting read and write only permission for user {username} to file {filepath}")

        command = CommandGenerator() \
            .icacls() \
            .parameters(f'"{filepath}"', "/inheritance:r", "/grant:r", f"{username}:RW")
        CommandExecutor().execute(command)
