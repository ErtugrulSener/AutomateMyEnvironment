import hashlib

from scripts.singleton import Singleton


@Singleton
class MD5Manager:
    def __init__(self):
        pass

    def hash(self, input):
        return hashlib.md5(input.encode("utf-8")).hexdigest()
