from win10toast import ToastNotifier

from scripts.singleton import Singleton


@Singleton
class WindowsNotificationManager(ToastNotifier):

    def send(self, title, text, icon_path=None, duration=5, threaded=False):
        self.show_toast(title, text, icon_path, duration, threaded)
