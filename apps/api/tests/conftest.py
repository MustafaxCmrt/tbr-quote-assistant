"""Each integration test gets a fresh database on the isolated test-db service.

Databases are retained for diagnosis; no reset or DROP command is issued.
"""

import asyncio
import os
from uuid import uuid4

import pytest_asyncio
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.persistence.database import database_url, make_engine


@pytest_asyncio.fixture
async def empty_db():
    base = database_url()
    if base.host != "test-db" or base.database != "tbr_test":
        raise RuntimeError("Tests require the isolated Compose test-db service.")
    name = "tbr_test_" + uuid4().hex
    admin = make_engine(base)
    async with admin.connect() as connection:
        connection = await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.execute(sa.text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()
    engine = make_engine(base.set(database=name))
    try:
        yield engine
    finally:
        await engine.dispose()


async def migrate(engine):
    previous = os.environ.get("POSTGRES_DB")
    os.environ["POSTGRES_DB"] = engine.url.database
    try:
        await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
    finally:
        if previous is None:
            os.environ.pop("POSTGRES_DB", None)
        else:
            os.environ["POSTGRES_DB"] = previous


@pytest_asyncio.fixture
async def db(empty_db):
    await migrate(empty_db)
    return empty_db
