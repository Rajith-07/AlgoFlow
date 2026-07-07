from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import connect_to_mongo, close_mongo_connection
from broker import connect_to_rabbitmq, close_rabbitmq_connection
from routers import submissions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up Gateway Service...")
    await connect_to_mongo()
    
    try:
        await connect_to_rabbitmq()
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        # In a real app we might retry or fail depending on strictness
        
    yield
    
    # Shutdown actions
    logger.info("Shutting down Gateway Service...")
    await close_rabbitmq_connection()
    await close_mongo_connection()

app = FastAPI(
    title="Submission Gateway Service",
    description="Entry point for remote code execution engine.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(submissions.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
