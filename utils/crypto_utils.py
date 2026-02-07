import os
from cryptography.fernet import Fernet
from pathlib import Path

class CryptoUtils:
    _key = None
    _cipher_suite = None

    @classmethod
    def initialize(cls):
        """Initializes the encryption key. 
        In a real app, this should be securely stored or obfuscated.
        For this prototype, we store it in a 'secret.key' file.
        """
        key_path = Path("secret.key")
        if key_path.exists():
            with open(key_path, "rb") as key_file:
                cls._key = key_file.read()
        else:
            cls._key = Fernet.generate_key()
            with open(key_path, "wb") as key_file:
                key_file.write(cls._key)
        
        cls._cipher_suite = Fernet(cls._key)

    @classmethod
    def encrypt(cls, data: str) -> bytes:
        if not cls._cipher_suite:
            cls.initialize()
        return cls._cipher_suite.encrypt(data.encode('utf-8'))

    @classmethod
    def decrypt(cls, encrypted_data: bytes) -> str:
        if not cls._cipher_suite:
            cls.initialize()
        return cls._cipher_suite.decrypt(encrypted_data).decode('utf-8')
