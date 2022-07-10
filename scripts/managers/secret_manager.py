import os
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

    def is_filetype(self, filepath, filetype):
        with open(filepath, "rb") as f:
            f.seek(1)
            found_filetype = f.read(len(filetype)).decode("utf-8")

            return found_filetype == filetype

    def is_encrypted(self, secret):
        return self.is_filetype(secret.value, "GITCRYPT")

    def is_git_cryptkey(self, filepath):
        return self.is_filetype(filepath, "GITCRYPTKEY")

    def lock(self):
        logger.info("Locking all secrets now...")

        command = CommandGenerator() \
            .parameters("git-crypt", "lock")
        CommandExecutor().execute(command)

    def unlock(self):
        logger.info("Unlocking all secrets now...")

        command = CommandGenerator() \
            .parameters("git-crypt", "unlock", "secret_decrypted")
        CommandExecutor().execute(command)
