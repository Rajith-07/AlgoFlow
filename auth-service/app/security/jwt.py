import os
import time
import base64
import jwt
from typing import Dict, Any
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from app.config.config import settings

# In-memory cached keys
_private_key: str = None
_public_key: str = None

def generate_key_pair(private_key_path: str, public_key_path: str) -> None:
    """Generates an RSA 2048-bit keypair and saves them as PEM files if they don't exist."""
    # Ensure directory structures exist
    priv_dir = os.path.dirname(private_key_path)
    pub_dir = os.path.dirname(public_key_path)

    if priv_dir:
        os.makedirs(priv_dir, exist_ok=True)
    if pub_dir:
        os.makedirs(pub_dir, exist_ok=True)

    if os.path.exists(private_key_path) and os.path.exists(public_key_path):
        return

    print("Generating a new RSA 2048 key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Serialize private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save to files
    with open(private_key_path, "wb") as f:
        f.write(pem_private)
    with open(public_key_path, "wb") as f:
        f.write(pem_public)
    print(f"Keys generated successfully at: {private_key_path} and {public_key_path}")

def load_keys() -> None:
    """Loads RSA private and public keys from file paths configured in settings."""
    global _private_key, _public_key
    
    # Resolve absolute paths
    priv_path = os.path.abspath(settings.JWT_PRIVATE_KEY_PATH)
    pub_path = os.path.abspath(settings.JWT_PUBLIC_KEY_PATH)

    # Auto-generate if missing
    generate_key_pair(priv_path, pub_path)

    with open(priv_path, "r", encoding="utf-8") as f:
        _private_key = f.read()

    with open(pub_path, "r", encoding="utf-8") as f:
        _public_key = f.read()

def get_private_key() -> str:
    """Returns the loaded private key PEM string, loading it if not cached."""
    if _private_key is None:
        load_keys()
    return _private_key

def get_public_key() -> str:
    """Returns the loaded public key PEM string, loading it if not cached."""
    if _public_key is None:
        load_keys()
    return _public_key

def create_access_token(user_id: str, username: str, role: str = "USER") -> str:
    """Creates a JWT access token using RS256, signed with the private key."""
    priv_pem = get_private_key()
    iat = int(time.time())
    exp = iat + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": iat,
        "exp": exp
    }
    
    # Sign with RS256 and inject a key identifier (kid) in the header
    token = jwt.encode(
        payload,
        priv_pem,
        algorithm=settings.JWT_ALGORITHM,
        headers={"kid": "auth-service-key"}
    )
    return token

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token using the public key."""
    pub_pem = get_public_key()
    try:
        payload = jwt.decode(
            token,
            pub_pem,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

def get_jwks() -> Dict[str, Any]:
    """Retrieves the public key formatted as a JSON Web Key Set (JWKS)."""
    pub_pem = get_public_key()
    
    # Parse public key object using cryptography
    pub_key_obj = load_pem_public_key(pub_pem.encode('utf-8'))
    numbers = pub_key_obj.public_numbers()
    
    # Helper to encode integers into base64url representation
    def int_to_base64url(val: int) -> str:
        val_bytes = val.to_bytes((val.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(val_bytes).decode('utf-8').rstrip('=')
    
    n_b64 = int_to_base64url(numbers.n)
    e_b64 = int_to_base64url(numbers.e)
    
    # Assemble standard RSA JWK structure
    jwk = {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "kid": "auth-service-key",
        "n": n_b64,
        "e": e_b64
    }
    
    return {"keys": [jwk]}