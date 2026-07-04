from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserSignup(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, description="Unique username")
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 900

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    expires_in: int = 900

class LogoutRequest(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
