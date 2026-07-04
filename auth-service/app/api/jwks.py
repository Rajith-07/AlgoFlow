from fastapi import APIRouter
from app.security.jwt import get_jwks

router = APIRouter()

@router.get("/.well-known/jwks.json")
async def jwks():
    """
    Returns the public key formatted as a JSON Web Key Set (JWKS).
    Allows other services to authenticate requests by verifying JWT signatures.
    """
    return get_jwks()
