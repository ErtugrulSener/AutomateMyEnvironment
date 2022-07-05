import ctypes
from ctypes import byref
from ctypes import c_int
from ctypes.wintypes import RGB

from scripts.managers.registry_manager import RegistryManager
from scripts.managers.registry_manager import RegistryPath
from scripts.singleton import Singleton
from scripts.software.configurator_base import ConfiguratorBase


@Singleton
class WindowsDesktopConfigurator(ConfiguratorBase):
    COLOR_BACKGROUND = 1

    SPI_SETDESKWALLPAPER = 0x14
    SPI_GETDESKWALLPAPER = 0x73

    def __init__(self):
        super().__init__(__file__)

    def has_wallpaper(self):
        dll = ctypes.WinDLL('user32')
        buf = ctypes.create_string_buffer(200)

        return dll.SystemParametersInfoA(self.SPI_GETDESKWALLPAPER, 200, buf, 0) and buf.value

    def get_background_color(self):
        background_color = ctypes.windll.user32.GetSysColor(self.COLOR_BACKGROUND)

        b = background_color & 255
        g = (background_color >> 8) & 255
        r = (background_color >> 16) & 255

        return [r, g, b]

    def has_not_black_background_color(self):
        r, g, b = self.get_background_color()
        return r != 0 or g != 0 or b != 0

    def set_background_color(self, color):
        if self.has_wallpaper():
            ctypes.windll.user32.SystemParametersInfoW(self.SPI_SETDESKWALLPAPER, 0, "", 3)
            RegistryManager.instance().set(RegistryPath.WINDOWS_WALLPAPER, "")

        if self.has_not_black_background_color():
            ctypes.windll.user32.SetSysColors(self.COLOR_BACKGROUND, byref(c_int(1)), byref(c_int(color)))

            r, g, b = self.get_background_color()
            RegistryManager.instance().set(RegistryPath.WINDOWS_BACKGROUND_COLOR, f"{r} {g} {b}")

    def is_configured_already(self):
        if self.has_wallpaper():
            return False

        if self.has_not_black_background_color():
            return False

        return True

    def configure(self):
        self.info("Setting desktop background color to plain black")
        self.set_background_color(RGB(0, 0, 0))
