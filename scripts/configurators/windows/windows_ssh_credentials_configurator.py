import os
import shutil

from winerror import ERROR_INVALID_FUNCTION

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.configurators.windows.windows_desktop_icon_configurator import DESKTOP_PATH
from scripts.managers.file_permission_manager import FilePermissionManager
from scripts.managers.secret_manager import Secret
from scripts.managers.secret_manager import SecretManager
from scripts.singleton import Singleton


@Singleton
class WindowsSSHCredentialsConfigurator(ConfiguratorBase):
    KEYS_FOLDER_PATH = r"secrets/keys"
    LOCAL_KEYS_FOLDER_PATH = os.path.join(DESKTOP_PATH, "keys")

    PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABAQCcG3VA0HWVhCZGFu2eGFS5dDFmB+iz7C6+MC4cv2dLtTg8+3hsXRtoYBwMd5AWg3Nn" \
                 "C4rnbL8jbT4mYdKA/UIPWMtTvV3D+k1UYuxE8aDdt2cQX2ziHtkpLyHXBVoGhwJTs7mpWomBO9DVH7fJH3ckfCA/nWJxyz" \
                 "JL2r/ZE/TvJAtK+EEJ4oei+Fmcl/T5SftdzliCoYrppV0ptTL3qxGSuotUzvwBcv6/xPntmkHIXjPK3d03KcNsVxzJbtg" \
                 "/oUZ7Db7/DWoXzTkZGNIqBTP2He/RRhT7FQ9l5V40Uprmjj+seiYHHbhPTM7OFZFpivSyumjryxaYjjV5Erxu3faF"

    def __init__(self):
        super().__init__(__file__)

        self.ssh_keys = []
        self.load_ssh_keys()

    def load_ssh_keys(self):
        command = CommandGenerator() \
            .parameters("ssh-add", "-L")

        output = CommandExecutor(expected_return_codes=[ERROR_INVALID_FUNCTION]).execute(command)

        if output.rstrip("\r\n") == "The agent has no identities.":
            return

        for line in output.splitlines():
            key_type, key, comment = line.split()
            self.ssh_keys.append(key)

    def is_configured_already(self):
        if self.PUBLIC_KEY not in self.ssh_keys:
            return False

        if not os.path.exists(self.LOCAL_KEYS_FOLDER_PATH):
            return False

        return True

    def configure(self):
        if self.PUBLIC_KEY not in self.ssh_keys:
            private_key_filepath = SecretManager.instance().get_filepath(Secret.PRIVATE_KEY_OPENSSH)

            self.info("Checking file permissions, setting to 600 (Only owner is allowed to read & write)")
            FilePermissionManager.instance().set_read_and_write_only(private_key_filepath, os.getlogin())

            self.info("Adding private key to windows ssh-agent")
            command = CommandGenerator() \
                .parameters("ssh-add", private_key_filepath)
            CommandExecutor().execute(command)

        if not os.path.exists(self.LOCAL_KEYS_FOLDER_PATH):
            self.info("Copying keys folder to desktop, to use later in configurations of software like PuTTy")
            shutil.copytree(self.KEYS_FOLDER_PATH, self.LOCAL_KEYS_FOLDER_PATH)
