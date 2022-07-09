from enum import Enum

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.singleton import Singleton
from scripts.logging.logger import Logger

logger = Logger.instance()


class Secret(Enum):
    PRIVATE_KEY_OPENSSH = r"keys/private_openssh"


@Singleton
class SecretManager:
    def __init__(self):
        pass

    def get_filepath(self, secret):
        return secret.value

    def is_encrypted(self, secret):
        filepath = secret.value

        with open(filepath, "rb") as f:
            f.seek(1)
            filetype = f.read(8).decode("utf-8")

            return filetype == "GITCRYPT"

    def lock(self):
        logger.info("Locking all secrets now.")

        command = CommandGenerator() \
                    .parameters("git-crypt", "lock")
        CommandExecutor().execute(command)

    def unlock(self):
        logger.info("Unlocking all secrets now.")

        command = CommandGenerator() \
                    .parameters("git-crypt", "unlock")
        CommandExecutor().execute(command)