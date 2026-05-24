from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
import logging
from sqlalchemy import text

logger = logging.getLogger("app.database")

# Initialize async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # checks connection health before issuing queries
    echo=False          # set to True for SQL log debugging if needed
)

# Async session maker factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """FastAPI Dependency for database sessions."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def check_db_connection():
    """Verify connectivity with Supabase PostgreSQL."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Successfully connected to Supabase PostgreSQL.")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False
