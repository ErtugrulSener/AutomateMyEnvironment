from win10toast import ToastNotifier

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class WindowsNotificationManager(ToastNotifier):

    def send(self, title, text, icon_path=None, duration=5, threaded=False):
        self.show_toast(title, text, icon_path, duration, threaded)
