from app.api.endpoints import router as auth_router
from app.api.jwks import router as jwks_router

__all__ = ["auth_router", "jwks_router"]
