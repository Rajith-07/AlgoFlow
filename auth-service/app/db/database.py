from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    """
    Dependency to get an async SQLAlchemy session.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
