"""
Fernet-based symmetric encryption helpers for storing passwords,
and a cryptographically secure password generator.
"""

import os
import secrets
import string
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


def generate_password(
    length: int = 16,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
) -> str:
    """Generate a cryptographically secure random password.

    Args:
        length:    Total number of characters (minimum 4, maximum 128).
        uppercase: Include uppercase letters (A-Z).
        numbers:   Include digits (0-9).
        symbols:   Include punctuation characters.

    Returns:
        A random password string of the requested length.

    Raises:
        ValueError: If no character class is selected or length is out of range.
    """
    if length < 4 or length > 128:
        raise ValueError("Password length must be between 4 and 128.")

    alphabet = string.ascii_lowercase
    required: list[str] = [secrets.choice(string.ascii_lowercase)]

    if uppercase:
        alphabet += string.ascii_uppercase
        required.append(secrets.choice(string.ascii_uppercase))
    if numbers:
        alphabet += string.digits
        required.append(secrets.choice(string.digits))
    if symbols:
        alphabet += string.punctuation
        required.append(secrets.choice(string.punctuation))

    if len(required) > length:
        raise ValueError("Length is too short to satisfy all character-class requirements.")

    # Fill remaining characters from the full alphabet
    remaining = [secrets.choice(alphabet) for _ in range(length - len(required))]
    password_chars = required + remaining
    # Shuffle using cryptographically secure Fisher-Yates
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]
    return "".join(password_chars)
