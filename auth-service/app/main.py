from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import auth_router, jwks_router
from app.security.jwt import load_keys

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Auth Service...")
    # Initialize RSA key pair (loads keys from file or generates them if not present)
    load_keys()
    
    yield
    
    print("Shutting down Auth Service...")

app = FastAPI(
    title="Authentication Service",
    description="Authentication and Identity Microservice for RCE Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes
app.include_router(auth_router)
app.include_router(jwks_router)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "auth"}