from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    return Fernet(get_settings().token_encryption_key.encode())


def encrypt_token(raw_token: str) -> str:
    return _fernet().encrypt(raw_token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return _fernet().decrypt(encrypted_token.encode()).decode()
