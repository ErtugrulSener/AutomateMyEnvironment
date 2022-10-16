from hashlib import sha256

from scripts.singleton import Singleton


@Singleton
class SHA256Manager:
    def hash(self, input_text):
        return sha256(input_text.encode('utf-8')).hexdigest()
