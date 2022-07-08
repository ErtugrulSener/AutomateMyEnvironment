from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class FilePermissionManager:
    @staticmethod
    def remove_permission(filepath, username):
        logger.info(f"Removing permission for user {username} to file {filepath}")
        command = CommandGenerator() \
            .CACLS() \
            .parameters(f'"{filepath}"', "/e", "/r", username)
        CommandExecutor().execute(command)

    @staticmethod
    def set_read_only(filepath, username):
        logger.info(f"Setting read only permission for user {username} to file {filepath}")
        command = CommandGenerator() \
            .icacls() \
            .parameters(f'"{filepath}"', "/inheritance:r", "/grant:r", f"{username}:R")
        CommandExecutor().execute(command)

