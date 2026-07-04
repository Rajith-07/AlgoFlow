import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import settings
from app.models.user import User, RefreshToken, utc_now
from app.schemas.user import UserSignup, UserLogin
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token

def hash_token(token: str) -> str:
    """Computes the SHA-256 hash of a string token for secure storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

async def signup_user(db: AsyncSession, user_data: UserSignup) -> User:
    """
    Registers a new user after verifying that the username and email are unique.
    Hashes the user password using Argon2id.
    """
    # Check if username is taken
    stmt = select(User).where(User.username == user_data.username)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email is taken
    stmt = select(User).where(User.email == user_data.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_pw = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_pw
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def login_user(db: AsyncSession, login_data: UserLogin) -> dict:
    """
    Authenticates a user, signs a new RS256 access JWT, generates a cryptographically
    secure random opaque refresh token, hashes it, and saves the hash in the database.
    """
    # Find user by email
    stmt = select(User).where(User.email == login_data.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(user.password_hash, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Issue access token
    access_token = create_access_token(user_id=str(user.id), username=user.username)

    # Issue refresh token (opaque random hex string)
    raw_refresh_token = secrets.token_hex(32)
    hashed_refresh_token = hash_token(raw_refresh_token)

    # Compute expiry date
    expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Save token hash
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh_token,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    """
    Validates a hashed refresh token, checking that it exists, is not revoked,
    and has not expired. Returns a new access JWT.
    """
    hashed_token = hash_token(refresh_token)
    
    # Query token
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed_token)
    res = await db.execute(stmt)
    db_token = res.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if db_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    if db_token.expires_at < utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    # Fetch associated user
    stmt = select(User).where(User.id == db_token.user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with refresh token not found"
        )

    # Issue new access token
    new_access_token = create_access_token(user_id=str(user.id), username=user.username)

    return {
        "access_token": new_access_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

async def logout_user(db: AsyncSession, refresh_token: str) -> None:
    """Revokes a refresh token by setting its revoked field to True."""
    hashed_token = hash_token(refresh_token)
    
    # Query token
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed_token)
    res = await db.execute(stmt)
    db_token = res.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )

    db_token.revoked = True
    await db.commit()
