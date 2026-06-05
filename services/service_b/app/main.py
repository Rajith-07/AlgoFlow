from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    description="Microservice B for AlgoFlow_AI",
    version="0.1.0",
    debug=settings.debug
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}!",
        "docs_url": "/docs",
        "health_check": "/health"
    }
