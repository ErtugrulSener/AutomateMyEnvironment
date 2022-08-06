import os
from pathlib import Path

from scripts.configurators.configurator_base import ConfiguratorBase
from scripts.managers.software_manager import SoftwareManager
from scripts.singleton import Singleton


@Singleton
class BraveConfigurator(ConfiguratorBase):
    SOFTWARE = "brave"

    def __init__(self):
        super().__init__(__file__)

        self.user_data_path = os.path.join(SoftwareManager.instance().get_persist_path(self.SOFTWARE), "User Data")
        self.first_run_filepath = os.path.join(self.user_data_path, "First Run")

    def first_run_file_exists(self):
        return os.path.exists(self.first_run_filepath)

    def is_configured_already(self):
        if not self.first_run_file_exists():
            return False

        return True

    def configure(self):
        if not self.first_run_file_exists():
            self.info(f"Create 'First Run' file for Brave to not ask to set as default browser on first startup")
            Path(self.first_run_filepath).touch()
