import os

from winregistry import WinRegistry

from scripts.logger import Logger
from scripts.software.configurator import Configurator
from scripts.software_installer import SoftwareInstaller

logger = Logger.instance()


class CmderConfigurator(Configurator):
    REG_PATHS = {
        "left_panel_directory": r"HKEY_CLASSES_ROOT\Directory\Background\shell\cmder",
        "right_panel_directory": r"HKEY_CLASSES_ROOT\Directory\shell\cmder",
    }

    def __init__(self):
        super().__init__(__file__)

    def configure(self):
        self.info("Adding 'open cmder here' to context menu for left panel")
        with WinRegistry() as client:
            left_panel_directory = self.REGEDIT_PATHS["left_panel_directory"]

            client.create_key(left_panel_directory)
            client.write_entry(left_panel_directory, "Icon",
                               os.path.join(SoftwareInstaller.instance().get_path("cmder"), r"icons\cmder.ico"))

            self.info(f"Wrote entry: {client.read_entry(left_panel_directory, 'Icon')}")

        self.info("Adding 'open cmder here' to context menu for right panel")
