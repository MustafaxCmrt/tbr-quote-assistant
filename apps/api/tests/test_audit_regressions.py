"""Full-audit regressions: real HTTP chat, fresh PostgreSQL, persisted effects only."""

import pytest
import sqlalchemy as sa

from app.persistence.models import mutation_receipts, quote_items, tool_call_logs
from tests.test_chat import chat_client, message, open_session

MUTATIONS = {"add_to_quote", "update_quote_item", "replace_with_alternative"}
CUSTOMERS = {
    "Q-1001": "CUST-IST-001",
    "Q-1002": "CUST-ANK-002",
    "Q-1004": "CUST-IST-001",
    "Q-1005": "CUST-IST-001",
}


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


# B06: a stated but unresolved quantity is asked about, never defaulted or sign-flipped.
@pytest.mark.parametrize(
    "text,quote",
    [
        ("BlueScan Air iki adet ekle.", "Q-1002"),
        ("BlueScan Air birkaç tane ekle.", "Q-1002"),
        ("BlueScan Air −2 adet ekle.", "Q-1002"),
        ("BlueScan Air –2 adet ekle.", "Q-1002"),
        ("BlueScan Air 2–3 adet ekle.", "Q-1002"),
        ("BlueScan Air x2 adet ekle.", "Q-1002"),
        ("Kablosuz okuyucudan iki tane daha ekle.", "Q-1001"),
    ],
)
async def test_unresolved_quantity_never_mutates(db, text, quote):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert_unchanged(data, before, after, logs, receipts)


@pytest.mark.parametrize(
    "text,quantity",
    [("BlueScan Air 2 adet ekle.", 2), ("BlueScan Air bir tane ekle.", 1)],
)
async def test_resolved_quantity_still_adds(db, text, quantity):
    data, before, after, _, receipts, _ = await run(db, text)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", quantity)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1


PRICE_CLARIFICATIONS = [
    # B01: every money expression must be understood, not just the first TL amount.
    "BlueScan Air 8.500 TL altında 1 adet ekle; bütçem 5.000 lira.",
    "BlueScan Air 8.500 TL altında öner; bütçem 5.000 lira.",
    "BlueScan Air 8.500 TL altında 1 adet ekle, en fazla ₺5.000 olsun.",
    "BlueScan Air 8.500 TL altında 1 adet ekle; 5 bin TL'yi geçmesin.",
    # B02: an explicit total budget is not a unit-price ceiling.
    "Toplam bütçem 9.000 TL, 2 adet BlueScan Air ekle.",
    "2 adet BlueScan Air ekle, toplam tutar 9.000 TL'yi geçmesin.",
    "Toplamda 9.000 TL altında 2 adet BlueScan Air öner.",
    "Bütçem 9.000 TL, 2 adet BlueScan Air ekle.",
]


@pytest.mark.parametrize("text", PRICE_CLARIFICATIONS)
async def test_unresolved_or_total_price_scope_never_recommends_or_mutates(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)
    assert "değiştirmedim" in data["notice"]
    assert data["recommended_product_ids"] == []
    assert "search_products" not in {log["tool_name"] for log in logs}


@pytest.mark.parametrize(
    "text,quote,expected",
    [
        ("Birim fiyatı 9.000 TL altında 2 adet BlueScan Air ekle.", "Q-1002", 2),
        ("BlueScan Air toplam 3 adet olsun, birim fiyatı 9.000 TL altında.", "Q-1001", 3),
    ],
)
async def test_unit_ceiling_with_quantity_still_adds(db, text, quote, expected):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", expected)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    adds = [log for log in logs if log["tool_name"] == "add_to_quote"]
    assert len(adds) == 1 and adds[0]["mutation_applied"]
