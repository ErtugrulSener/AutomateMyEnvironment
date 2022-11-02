import requests

from scripts.singleton import Singleton


@Singleton
class NetworkManager:
    def has_internet_connection(self):
        try:
            _ = requests.head("https://8.8.8.8", timeout=5)
            return True
        except requests.ConnectionError:
            return False
