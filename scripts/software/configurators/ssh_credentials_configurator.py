import os

import psutil as psutil

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.managers.file_permission_manager import FilePermissionManager
from scripts.singleton import Singleton
from scripts.software.configurator_base import ConfiguratorBase


@Singleton
class SSHCredentialsConfigurator(ConfiguratorBase):
    PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABAQCcG3VA0HWVhCZGFu2eGFS5dDFmB+iz7C6+MC4cv2dLtTg8+3hsXRtoYBwMd5AWg3Nn" \
                 "C4rnbL8jbT4mYdKA/UIPWMtTvV3D+k1UYuxE8aDdt2cQX2ziHtkpLyHXBVoGhwJTs7mpWomBO9DVH7fJH3ckfCA/nWJxyz" \
                 "JL2r/ZE/TvJAtK+EEJ4oei+Fmcl/T5SftdzliCoYrppV0ptTL3qxGSuotUzvwBcv6/xPntmkHIXjPK3d03KcNsVxzJbtg" \
                 "/oUZ7Db7/DWoXzTkZGNIqBTP2He/RRhT7FQ9l5V40Uprmjj+seiYHHbhPTM7OFZFpivSyumjryxaYjjV5Erxu3faF"

    def __init__(self):
        super().__init__(__file__)

        self.ssh_keys = []
        self.refresh_ssh_keys_cache()

    def refresh_ssh_keys_cache(self):
        command = CommandGenerator() \
            .parameters("ssh-add", "-L")

        first_time_loading = len(self.ssh_keys) == 0
        output = CommandExecutor(print_to_console=not first_time_loading).execute(command)

        for line in output.splitlines():
            key_type, key, comment = line.split()
            self.ssh_keys.append(key)

    def is_configured_already(self):
        return self.PUBLIC_KEY in self.ssh_keys

    def configure(self):
        # TODO: Download private key with git-secrets here
        private_key_path = os.path.join(os.path.join(os.environ['USERPROFILE']), r'Desktop\private_openssh')

        self.info("Checking file permissions, setting to 600 (Only owner is allowed to read)")

        users = psutil.users()
        for user in users:
            FilePermissionManager.instance().remove_permission(private_key_path, user.name)

        FilePermissionManager.instance().set_read_only(private_key_path, os.getlogin())

        self.info("Adding private key to windows ssh-agent")

        command = CommandGenerator() \
            .parameters("ssh-add", private_key_path)
        CommandExecutor().execute(command)
