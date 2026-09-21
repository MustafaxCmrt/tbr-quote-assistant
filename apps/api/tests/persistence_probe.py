"""Cross-process restart proof on a dedicated, non-destructively retained test DB."""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa

from app.persistence.database import database_url, make_engine
from app.persistence.models import (
    chat_messages,
    chat_sessions,
    metadata,
    mutation_receipts,
    products,
    quote_items,
)
from app.persistence.seed import load_seed, seed_database
from tests.conftest import migrate

EVIDENCE = Path("/evidence/persistence.json")


async def snapshot(engine):
    async with engine.connect() as connection:
        return {
            table.name: [
                dict(row)
                for row in (
                    await connection.execute(sa.select(table).order_by(*table.primary_key.columns))
                ).mappings()
            ]
            for table in metadata.sorted_tables
        }


async def main():
    base = database_url()
    assert base.host == "test-db" and base.database == "tbr_test"
    if sys.argv[1] == "prepare":
        name = "tbr_test_persistence_" + uuid4().hex
        admin = make_engine(base)
        async with admin.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(sa.text(f'CREATE DATABASE "{name}"'))
        await admin.dispose()
        engine = make_engine(base.set(database=name))
        await migrate(engine)
        await seed_database(engine)
        rows, _ = load_seed()
        item = rows["quote_items"][0]
        quote = next(row for row in rows["quotes"] if row["quote_id"] == item["quote_id"])
        async with engine.begin() as conn:
            await conn.execute(
                products.update()
                .where(products.c.product_id == item["product_id"])
                .values(notes="Kalıcılık kanıtı")
            )
            await conn.execute(
                quote_items.update()
                .where(quote_items.c.quote_item_id == item["quote_item_id"])
                .values(quantity=7)
            )
            await conn.execute(
                chat_sessions.insert().values(
                    session_id="persist-session",
                    quote_id=quote["quote_id"],
                    customer_id=quote["customer_id"],
                    channel="web",
                    locale="tr",
                )
            )
            await conn.execute(
                chat_messages.insert().values(
                    session_id="persist-session",
                    message_id="persist-message",
                    body="Kalıcılık testi",
                    payload_hash="probe",
                )
            )
            await conn.execute(
                mutation_receipts.insert().values(
                    quote_id=quote["quote_id"],
                    idempotency_key="persist-key",
                    session_id="persist-session",
                    message_id="persist-message",
                    action_index=0,
                    operation="update_quote_item",
                    payload_hash="probe",
                    committed_version=1,
                    result={"quantity": 7},
                )
            )
        EVIDENCE.write_text(
            json.dumps(
                {"database": name, "snapshot": await snapshot(engine)},
                default=str,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        print(
            "PASS: dedicated DB seeded; user edit, quantity and receipt committed; baseline saved."
        )
    else:
        evidence = json.loads(EVIDENCE.read_text())
        engine = make_engine(base.set(database=evidence["database"]))
        # Compare once immediately after restart, and again after repeated startup seed.
        actual = json.loads(json.dumps(await snapshot(engine), default=str))
        assert actual == evidence["snapshot"], "Restart changed persisted state"
        inserted = await seed_database(engine)
        assert all(value == 0 for value in inserted.values()), inserted
        actual = json.loads(json.dumps(await snapshot(engine), default=str))
        assert actual == evidence["snapshot"], "Repeated seed changed persisted state"
        print(
            "PASS: all tables, edits and mutation receipt survived restart and repeated seed unchanged."
        )
    await engine.dispose()


asyncio.run(main())
