from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
import logging
import ssl
from sqlalchemy import text

logger = logging.getLogger("app.database")

# Strip leading/trailing whitespaces and ?ssl=require from URL
_db_url = settings.DATABASE_URL.strip().replace("?ssl=require", "").replace("&ssl=require", "")

# Build SSL context for Supabase / any PostgreSQL requiring SSL
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

_connect_args = {
    "statement_cache_size": 0
}
if "supabase" in _db_url or "pooler" in _db_url:
    _connect_args["ssl"] = _ssl_context

# Initialize async engine for PostgreSQL
engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
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
