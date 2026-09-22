"""Full-audit regressions: real HTTP chat, fresh PostgreSQL, persisted effects only."""

import pytest
import sqlalchemy as sa

from app.persistence.models import mutation_receipts, quote_items, tool_call_logs
from tests.test_chat import chat_client, message, open_session

MUTATIONS = {"add_to_quote", "update_quote_item", "replace_with_alternative"}
CUSTOMERS = {"Q-1002": "CUST-ANK-002", "Q-1004": "CUST-IST-001", "Q-1005": "CUST-IST-001"}


async def run(db, text, quote="Q-1002"):
    app, client = await chat_client(db)
    async with app.router.lifespan_context(app), client:
        sid = await open_session(client, quote, CUSTOMERS[quote])
        before = (await client.get(f"/api/quotes/{quote}")).json()
        response = await client.post("/api/chat", json=message(sid, text, quote))
        assert response.status_code == 200, response.text
        after = (await client.get(f"/api/quotes/{quote}")).json()
    async with db.connect() as conn:
        logs = (
            (await conn.execute(sa.select(tool_call_logs).order_by(tool_call_logs.c.log_id)))
            .mappings()
            .all()
        )
        receipts = (await conn.execute(sa.select(mutation_receipts))).mappings().all()
        rows = (
            (await conn.execute(sa.select(quote_items).where(quote_items.c.quote_id == quote)))
            .mappings()
            .all()
        )
    return response.json(), before, after, logs, receipts, rows


def assert_unchanged(data, before, after, logs, receipts):
    assert data["notice"]
    assert after == before and receipts == []
    assert not MUTATIONS & {log["tool_name"] for log in logs}


def items(quote):
    return [(p["product_id"], p["quantity"]) for p in quote["items"]]


# B03: a mentioned command is not an instruction to mutate.
@pytest.mark.parametrize(
    "text",
    [
        '"BlueScan Air 1 adet ekle" cümlesi ne anlama geliyor?',
        "“BlueScan Air 1 adet ekle” ne demek?",
        "BlueScan Air 1 adet ekle dersem iade koşulları ne olur?",
        "BlueScan Air 1 adet eklersem iade koşulları ne olur?",
        "BlueScan Air 1 adet ekle ama önce benden onay iste.",
        "Önce bana sor, sonra BlueScan Air 1 adet ekle.",
        "BlueScan Air 1 adet ekle; onayımı bekle.",
    ],
)
async def test_quoted_hypothetical_or_approval_command_never_mutates(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)
    assert "Teklifi değiştirmedim" in data["notice"]


async def test_hypothetical_policy_question_still_answers_from_knowledge(db):
    data, before, after, logs, receipts, _ = await run(
        db, "BlueScan Air 1 adet ekle dersem iade koşulları ne olur?"
    )
    assert_unchanged(data, before, after, logs, receipts)
    entries = [
        e["knowledge_id"]
        for log in logs
        if log["tool_name"] == "get_knowledge_entries" and log["input"]["topic"] == "return_policy"
        for e in log["output"]["entries"]
    ]
    assert entries
    assert set(entries) <= {s["source_id"] for s in data["sources"] if s["kind"] == "knowledge"}


@pytest.mark.parametrize(
    "text",
    [
        "BlueScan Air 1 adet ekle.",
        '"BlueScan Air" 1 adet ekle.',
        "Onaylıyorum, BlueScan Air 1 adet ekle.",
        "Onay alındı, BlueScan Air 1 adet ekle.",
        "Bana sormadan BlueScan Air 1 adet ekle.",
    ],
)
async def test_direct_command_still_adds_once(db, text):
    data, before, after, _, receipts, _ = await run(db, text)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", 1)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
