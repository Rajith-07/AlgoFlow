from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# PasswordHasher automatically uses Argon2id by default
ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hashes a plain text password using Argon2id."""
    return ph.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """Verifies a plain text password against an Argon2id hash."""
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
