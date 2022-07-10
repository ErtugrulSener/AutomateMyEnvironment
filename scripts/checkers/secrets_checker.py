import base64
import http.client as httplib

from scripts.logging.logger import Logger
from scripts.managers.aes_manager import AESManager
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SecretsChecker:
    def check_git_crypt_symmetric_key(self):
        logger.info('Checking if git-crypt symmetric key can be decrypted with given password')

        password = input("Password to decrypt the git-crypt symmetric key: ")

        with open("secret", "rb") as binary_file:
            binary_file_data = binary_file.read()
            try:
                decrypted = AESManager.instance().decrypt(binary_file_data, password).decode('utf-8')
            except Exception:
                logger.error("The password given to decrypt the git-crypt symmetric key was invalid!")
                exit(8)

            base64_decoded_data = base64.b64decode(decrypted)

        with open("secret_decrypted", "wb") as fw:
            fw.write(base64_decoded_data)

    def check(self):
        self.check_git_crypt_symmetric_key()
