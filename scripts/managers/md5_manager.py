import hashlib

from scripts.singleton import Singleton


@Singleton
class MD5Manager:
    def hash(self, input_text):
        return hashlib.md5(input_text.encode("utf-8")).hexdigest()
