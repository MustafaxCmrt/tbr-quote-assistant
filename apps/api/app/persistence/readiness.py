"""Readiness requires both the schema and the atomically committed seed marker."""

import asyncio

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from app.persistence.seed import SEED_ID

SCHEMA_VERSION = "0001"


async def is_ready(engine) -> bool:
    if engine is None:
        return False
    try:
        async with asyncio.timeout(3):
            async with engine.connect() as connection:
                revision = await connection.scalar(
                    sa.text("SELECT version_num FROM alembic_version")
                )
                seeded = await connection.scalar(
                    sa.text(
                        "SELECT EXISTS (SELECT 1 FROM bootstrap_state WHERE seed_id = :seed_id)"
                    ),
                    {"seed_id": SEED_ID},
                )
                return revision == SCHEMA_VERSION and seeded is True
    except (SQLAlchemyError, OSError, TimeoutError):
        # Connection details and raw exceptions must not appear in public responses.
        return False
