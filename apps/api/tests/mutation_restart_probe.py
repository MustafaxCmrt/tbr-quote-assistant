"""Real wrapper replay across PostgreSQL restart; uses only a new isolated test DB."""

import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa

from app.persistence.database import database_url, make_engine
from app.persistence.models import mutation_receipts, tool_call_logs
from app.persistence.seed import seed_database
from app.services.executor import execute_plan
from tests.conftest import migrate
from tests.test_mutations import add, current, prepare

EVIDENCE = Path("/evidence/mutation_restart.json")


async def main():
    base = database_url()
    assert base.host == "test-db" and base.database == "tbr_test"
    if sys.argv[1] == "prepare":
        name = "tbr_test_replay_" + uuid4().hex
        admin = make_engine(base)
        async with admin.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(sa.text(f'CREATE DATABASE "{name}"'))
        await admin.dispose()
        engine = make_engine(base.set(database=name))
        await migrate(engine)
        await seed_database(engine)
        ids = await prepare(engine, [add()])
        await execute_plan(engine, *ids)
        quote = await current(engine)
        assert quote.items[0].quantity == 2
        EVIDENCE.write_text(
            json.dumps({"database": name, "ids": ids, "quote": quote.model_dump(mode="json")})
        )
        print(
            "PASS real add wrapper committed; initial quantity 1 -> 2, receipt and log persisted."
        )
    else:
        evidence = json.loads(EVIDENCE.read_text())
        engine = make_engine(base.set(database=evidence["database"]))
        await seed_database(engine)
        result = await execute_plan(engine, *evidence["ids"])
        assert result[0]["replayed"] is True and result[0]["mutation_applied"] is False
        assert (await current(engine)).model_dump(mode="json") == evidence["quote"]
        async with engine.connect() as conn:
            assert await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts)) == 1
            logs = (
                await conn.execute(
                    sa.select(
                        tool_call_logs.c.replayed, tool_call_logs.c.mutation_applied
                    ).order_by(tool_call_logs.c.log_id)
                )
            ).all()
            assert logs == [(False, True), (True, False)]
        print(
            "PASS after PostgreSQL restart + seed: actual add wrapper replay, quantity/version unchanged, 1 receipt, 2 real attempt logs."
        )
    await engine.dispose()


asyncio.run(main())
