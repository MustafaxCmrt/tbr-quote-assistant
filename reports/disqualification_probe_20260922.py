"""Review probes through HTTP and fresh isolated PostgreSQL databases; no demo reset."""
import asyncio
import json
from decimal import Decimal
from uuid import uuid4

import httpx
import sqlalchemy as sa

from app.main import create_app
from app.persistence.database import database_url, make_engine
from app.persistence.models import chat_messages, mutation_receipts, tool_call_logs
from app.persistence.seed import seed_database
from tests.conftest import migrate


CASES = [
    ("read_ceiling_lira", "8.500 lirayı geçmeyen endüstriyel barkod okuyucu öner.", "Q-1001", "CUST-IST-001", "8500"),
    ("read_ceiling_tl_control", "8.500 TL altında endüstriyel barkod okuyucu öner.", "Q-1001", "CUST-IST-001", "8500"),
    ("read_ceiling_missing_marker", "Bütçem 8.500 TL. BlueScan Pro önerir misin?", "Q-1001", "CUST-IST-001", "8500"),
    ("negated_backorder", "PRD-BC-130 1 adet ekle, bekleyebilirim demiyorum.", "Q-1002", "CUST-ANK-002", None),
    ("absent_backorder_control", "PRD-BC-130 1 adet ekle.", "Q-1002", "CUST-ANK-002", None),
    ("positive_backorder_control", "PRD-BC-130 1 adet ekle, bekleyebilirim.", "Q-1002", "CUST-ANK-002", None),
    ("policy_return", "Aktive edilen yazılım lisansını iade edebilir miyim?", "Q-1001", "CUST-IST-001", None),
    ("policy_compatibility", "Starter lisansı offline çalışır mı?", "Q-1001", "CUST-IST-001", None),
]


async def main():
    base = database_url()
    if base.host != "test-db" or base.database != "tbr_test":
        raise RuntimeError("Only isolated test-db/tbr_test is permitted")
    results = []
    for name, text, quote_id, customer_id, ceiling in CASES:
        db_name = "tbr_test_audit_" + uuid4().hex
        admin = make_engine(base)
        async with admin.connect() as conn:
            conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
        await admin.dispose()
        engine = make_engine(base.set(database=db_name))
        await migrate(engine)
        await seed_database(engine)
        app = create_app(engine)
        async with app.router.lifespan_context(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            before = (await client.get(f"/api/quotes/{quote_id}")).json()
            session = await client.post("/api/chat/sessions", json={"quote_id": quote_id, "customer_id": customer_id})
            if session.status_code != 201:
                raise RuntimeError(f"Invalid probe context: {name}, {session.status_code}")
            sid = session.json()["session_id"]
            mid = uuid4().hex
            response = await client.post("/api/chat", json={"session_id": sid, "quote_id": quote_id, "message_id": mid, "message": text})
            after = (await client.get(f"/api/quotes/{quote_id}")).json()
            async with engine.connect() as conn:
                logs = (await conn.execute(sa.select(tool_call_logs).where(tool_call_logs.c.session_id == sid).order_by(tool_call_logs.c.log_id))).mappings().all()
                stored = (await conn.execute(sa.select(chat_messages).where(chat_messages.c.session_id == sid))).mappings().one()
                receipts = await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts))
            recommendations = [p for log in logs if log["tool_name"] == "search_products" for p in log["output"]["recommendations"]]
            result = {"case": name, "database": db_name, "message": text, "http_status": response.status_code,
                "response": response.json(), "before": before, "after": after,
                "quote_changed": before != after, "receipt_count": receipts,
                "trusted_constraints": stored["trusted_constraints"],
                "tool_flags": [{k: log[k] for k in ("tool_name", "replayed", "mutation_applied")} for log in logs],
                "over_ceiling_recommendations": [{k: p[k] for k in ("product_id", "price_try")} for p in recommendations if ceiling is not None and Decimal(p["price_try"]) > Decimal(ceiling)]}
            results.append(result)
            print(json.dumps({k: result[k] for k in ("case", "http_status", "quote_changed", "receipt_count", "trusted_constraints", "over_ceiling_recommendations")}, ensure_ascii=False), flush=True)
        await engine.dispose()
    with open("/evidence/disqualification_probe_20260922.json", "w") as output:
        json.dump(results, output, ensure_ascii=False, indent=2, default=str)


asyncio.run(main())
