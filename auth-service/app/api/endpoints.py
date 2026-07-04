from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import (
    UserSignup,
    UserLogin,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    LogoutRequest,
    UserOut
)
import app.services.auth as auth_service

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: AsyncSession = Depends(get_db)):
    """Registers a new user account with hashed password credentials."""
    user = await auth_service.signup_user(db, user_data)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticates user credentials and issues new access and refresh tokens."""
    result = await auth_service.login_user(db, login_data)
    return result

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh(refresh_data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Validates an opaque refresh token and generates a new RS256 access JWT."""
    result = await auth_service.refresh_access_token(db, refresh_data.refresh_token)
    return result

@router.post("/logout")
async def logout(logout_data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    """Revokes the provided refresh token so it can no longer be used for credential renewal."""
    await auth_service.logout_user(db, logout_data.refresh_token)
    return {"message": "Successfully logged out"}
