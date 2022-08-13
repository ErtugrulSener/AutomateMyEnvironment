import os

from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class FileAssociationManager:
    SET_USER_FTA_LOCAL_PATH = os.path.join(os.getcwd(), r"external/executables/set-user-fta/SetUserFTA.exe")

    def __init__(self):
        self.associated_file_extensions = {}
        self.load_associated_file_extensions()

    def load_associated_file_extensions(self):
        command = CommandGenerator() \
            .parameters(self.SET_USER_FTA_LOCAL_PATH, "get")

        output = CommandExecutor().execute(command)

        for line in output.splitlines():
            extension, association = line.split(", ")
            self.associated_file_extensions[extension] = association

    def get(self, extension):
        return self.associated_file_extensions.get(extension)
