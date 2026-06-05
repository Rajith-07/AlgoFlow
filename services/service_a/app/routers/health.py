from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment
    }
