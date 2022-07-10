# -*- coding: utf-8 -*-
import pyaes
from scripts.singleton import Singleton

BLOCK_SIZE = 16


@Singleton
class AESManager:
	def encrypt(self, text, key):
		if not text:
			return ""

		aes = pyaes.AESModeOfOperationCTR(key.encode())
		text = self.pad(text)
		encrypted = aes.encrypt(text)
		return encrypted

	def decrypt(self, text, key):
		if not text:
			return ""

		aes = pyaes.AESModeOfOperationCTR(key.encode())
		decrypted = self.reverse_pad(aes.decrypt(text))
		return decrypted

	def pad(self, s):
		return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)

	def reverse_pad(self, s):
		return s[:-ord(s[len(s)-1:])]
