from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# Async database setup
async_engine = create_async_engine(
    settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=True
)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync database setup
sync_engine = create_engine(
    settings.sync_database_url,
    echo=True)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Legacy exports for backward compatibility
engine = sync_engine
SessionLocal = SyncSessionLocal

Base = declarative_base()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session


def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Legacy function for backward compatibility
def get_db():
    """Legacy function that returns sync database session"""
    return get_sync_db()
