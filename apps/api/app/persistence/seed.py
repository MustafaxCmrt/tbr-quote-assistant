"""Insert missing original IDs, never overwrite edits or remove rows."""

import asyncio
import hashlib
import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from app.persistence.database import make_engine
from app.persistence.models import SEED_TABLES, bootstrap_state

SEED_ID = "tbr-source-v1"
SOURCE_DIR = Path(os.getenv("SEED_SOURCE_DIR", Path(__file__).resolve().parents[4] / "data/source"))


def load_seed(source_dir=SOURCE_DIR):
    records = {}
    digest = hashlib.sha256()
    for table in SEED_TABLES:
        raw = (source_dir / f"{table.name}.json").read_bytes()
        digest.update(table.name.encode() + b"\0" + raw)
        rows = json.loads(raw, parse_float=Decimal)
        for row in rows:
            for column in table.columns:
                if column.name not in row:
                    continue
                if isinstance(column.type, sa.Numeric):
                    row[column.name] = Decimal(str(row[column.name]))
                elif isinstance(column.type, sa.Date):
                    row[column.name] = date.fromisoformat(row[column.name])
        records[table.name] = rows
    stocks = {row["product_id"]: row["stock_qty"] for row in records["products"]}
    for item in records["quote_items"]:
        item["fulfillment_status"] = (
            "out_of_stock" if stocks[item["product_id"]] == 0 else "in_stock"
        )
    return records, digest.hexdigest()


async def seed_connection(connection, source_dir=SOURCE_DIR):
    """Caller owns transaction; marker and every row commit or roll back together."""
    records, digest = load_seed(source_dir)
    await connection.execute(sa.text("SELECT pg_advisory_xact_lock(714260921)"))
    inserted = {}
    for table in SEED_TABLES:
        statement = (
            insert(table)
            .values(records[table.name])
            .on_conflict_do_nothing(index_elements=list(table.primary_key.columns))
            .returning(next(iter(table.primary_key.columns)))
        )
        inserted[table.name] = len((await connection.execute(statement)).all())
    await connection.execute(
        insert(bootstrap_state)
        .values(seed_id=SEED_ID, source_sha256=digest)
        .on_conflict_do_nothing(index_elements=["seed_id"])
    )
    return inserted


async def seed_database(engine, source_dir=SOURCE_DIR):
    async with engine.begin() as connection:
        return await seed_connection(connection, source_dir)


async def main():
    engine = make_engine()
    try:
        print(json.dumps(await seed_database(engine), ensure_ascii=False))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
