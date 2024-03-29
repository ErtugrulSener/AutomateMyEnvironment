from enum import Enum

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton


class Secret(Enum):
    PRIVATE_KEY_OPENSSH = r"secrets/keys/private_openssh"


@Singleton
class SecretManager:
    def __init__(self):
        self.logger = Logger.instance()

    def get_filepath(self, secret):
        return secret.value

    def get_content(self, secret, mode="r"):
        filepath = self.get_filepath(secret)
        content = open(filepath, mode)
        return content

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
        if self.is_encrypted(Secret.PRIVATE_KEY_OPENSSH):
            return

        self.logger.info("Locking all secrets now...")

        command = CommandGenerator() \
            .parameters("git-crypt", "lock")
        CommandExecutor().execute(command)

    def unlock(self):
        if not self.is_encrypted(Secret.PRIVATE_KEY_OPENSSH):
            return

        self.logger.info("Unlocking all secrets now...")

        command = CommandGenerator() \
            .parameters("git-crypt", "unlock", "secret_decrypted")
        CommandExecutor().execute(command)
