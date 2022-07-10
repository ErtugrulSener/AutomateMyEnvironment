import base64
import http.client as httplib
import os.path

import stdiomask

from scripts.logging.logger import Logger
from scripts.managers.aes_manager import AESManager
from scripts.managers.secret_manager import SecretManager
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class SecretsChecker:
    SECRET_ENCRYPTED_FILEPATH = r"secret"
    SECRET_DECRYPTED_FILEPATH = r"secret_decrypted"

    def check_git_crypt_symmetric_key(self):
        logger.info('Checking if git-crypt symmetric key can be decrypted with given password')

        if os.path.exists(self.SECRET_DECRYPTED_FILEPATH) and \
                SecretManager.instance().is_git_cryptkey(self.SECRET_DECRYPTED_FILEPATH):
            return

        password = stdiomask.getpass("Password to decrypt the git-crypt symmetric key: ", mask="*")

        with open(self.SECRET_ENCRYPTED_FILEPATH, "rb") as binary_file:
            binary_file_data = binary_file.read()
            try:
                decrypted = AESManager.instance().decrypt(binary_file_data, password).decode('utf-8')
            except Exception:
                logger.error("The password given to decrypt the git-crypt symmetric key was invalid!")
                exit(8)

            base64_decoded_data = base64.b64decode(decrypted)

        with open(self.SECRET_DECRYPTED_FILEPATH, "wb") as fw:
            fw.write(base64_decoded_data)

    def check(self):
        self.check_git_crypt_symmetric_key()
