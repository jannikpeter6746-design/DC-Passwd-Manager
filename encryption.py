"""
Fernet-based symmetric encryption helpers for storing passwords.
"""

import os
from cryptography.fernet import Fernet


def get_fernet() -> Fernet:
    """Return a Fernet instance using the key from the environment."""
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except Exception as exc:
        raise RuntimeError(
            f"ENCRYPTION_KEY is invalid (must be a 32-byte URL-safe base64-encoded Fernet key): {exc}"
        ) from exc


def encrypt_password(plaintext: str) -> str:
    """Encrypt a plaintext password and return the ciphertext as a string."""
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    """Decrypt a ciphertext password and return the plaintext string."""
    f = get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
