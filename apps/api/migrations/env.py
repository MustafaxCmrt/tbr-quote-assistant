import asyncio

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.persistence.database import database_url
from app.persistence.models import metadata


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_online():
    engine = create_async_engine(database_url(), poolclass=pool.NullPool, hide_parameters=True)
    async with engine.connect() as connection:
        await connection.exec_driver_sql("SELECT pg_advisory_lock(714260922)")
        await connection.commit()
        try:
            await connection.run_sync(run_migrations)
        finally:
            await connection.exec_driver_sql("SELECT pg_advisory_unlock(714260922)")
            await connection.commit()
    await engine.dispose()


if context.is_offline_mode():
    context.configure(
        url=database_url(),
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_online())
