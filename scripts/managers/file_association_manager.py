from scripts.commands.command_executor import CommandExecutor
from scripts.commands.command_generator import CommandGenerator
from scripts.constants.Enums import ExecutablePaths
from scripts.singleton import Singleton


@Singleton
class FileAssociationManager:
    def __init__(self):
        self.associated_file_extensions = {}
        self.load_associated_file_extensions()

    def load_associated_file_extensions(self):
        command = CommandGenerator() \
            .parameters(ExecutablePaths.SET_USER_TFA.value(), "get")

        output = CommandExecutor().execute(command)

        for line in output.splitlines():
            extension, association = line.split(", ")
            self.associated_file_extensions[extension] = association

    def get(self, extension):
        return self.associated_file_extensions.get(extension)
