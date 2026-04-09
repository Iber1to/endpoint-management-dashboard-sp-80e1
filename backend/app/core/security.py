from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and set it in your .env file."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def mask_token(token: str) -> str:
    if not token or len(token) < 8:
        return "****"
    return token[:4] + "****" + token[-4:]
