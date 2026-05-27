import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Ensure app package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import ssl
    _db_url = settings.DATABASE_URL.replace("?ssl=require", "").replace("&ssl=require", "")
    _connect_args = {
        "statement_cache_size": 0
    }
    if "supabase" in _db_url or "pooler" in _db_url:
        _ssl_ctx = ssl.create_default_context()
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = ssl.CERT_NONE
        _connect_args["ssl"] = _ssl_ctx
    connectable = create_async_engine(
        _db_url,
        poolclass=pool.NullPool,
        connect_args=_connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run in asyncio loop
    try:
        # Check if there is an active event loop
        loop = asyncio.get_running_loop()
        # If there is, we run in a task
        loop.create_task(run_migrations_online())
    except RuntimeError:
        # If no loop is running, use asyncio.run
        asyncio.run(run_migrations_online())
