from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.security.jwt import decode_access_token
from typing import Dict, Any

# OAuth2PasswordBearer extracts the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

async def get_current_user_claims(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and validate the current user's claims 
    from the authorization header's RS256 JWT access token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(token)
        return claims
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
