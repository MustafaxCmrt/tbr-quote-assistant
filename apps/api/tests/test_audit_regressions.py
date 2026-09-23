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


# B04: an explicit replacement target is honored exactly, or nothing changes.
@pytest.mark.parametrize(
    "text",
    [
        "BlueScan Pro ürününü GreenScan Eco ile değiştir.",
        "PRD-BC-120 ürününü PRD-BC-140 ile değiştir.",
        "Pahalı okuyucuyu GreenScan Eco'yla değiştir.",
        "BlueScan Pro'yu değiştir, yerine GreenScan Eco ekle.",
    ],
)
async def test_explicit_replace_target_is_the_exact_product(db, text):
    data, before, after, logs, receipts, rows = await run(db, text, "Q-1004")
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-140", 1)]
    assert [(p["product_id"], p["status"]) for p in after["history"]] == [("PRD-BC-120", "replaced")]
    assert sorted((r["product_id"], r["status"]) for r in rows) == [
        ("PRD-BC-120", "replaced"),
        ("PRD-BC-140", "active"),
    ]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    replaces = [log for log in logs if log["tool_name"] == "replace_with_alternative"]
    assert [(r["input"]["from_product_id"], r["input"]["to_product_id"]) for r in replaces] == [
        ("PRD-BC-120", "PRD-BC-140")
    ]


@pytest.mark.parametrize(
    "text",
    [
        # Not a registered substitute of PRD-BC-120.
        "BlueScan Pro ürününü BlueScan Lite ile değiştir.",
        # Out of stock, and not a registered substitute either.
        "BlueScan Pro ürününü RedScan Mini ile değiştir.",
        # Registered substitute, but above the explicit unit ceiling.
        "BlueScan Pro ürününü 5.000 TL altında BlueScan Air ile değiştir.",
        # Registered substitute, but lacks the required feature.
        "BlueScan Pro ürününü QR'lı GreenScan Eco ile değiştir.",
        # Two explicit targets.
        "BlueScan Pro ürününü GreenScan Eco ile veya BlueScan Air ile değiştir.",
    ],
)
async def test_unsatisfiable_or_ambiguous_explicit_target_never_substitutes(db, text):
    data, before, after, logs, receipts, _ = await run(db, text, "Q-1004")
    assert_unchanged(data, before, after, logs, receipts)
    assert "değiştirmedim" in data["notice"]


# B05: a clause after ';' keeps binding the product it follows.
@pytest.mark.parametrize(
    "text",
    [
        "BlueScan Lite 1 adet ekle; QR zorunlu.",
        "BlueScan Lite 1 adet ekle; kablosuz olmalı.",
        "BlueScan Air 1 adet ekle; GreenScan Eco'nun fiyatı ne?",
    ],
)
async def test_semicolon_clause_is_not_dropped(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)


@pytest.mark.parametrize(
    "text", ["BlueScan Air 1 adet ekle; QR zorunlu.", "QR zorunlu; BlueScan Air 1 adet ekle."]
)
async def test_semicolon_feature_is_enforced_at_mutation(db, text):
    from app.persistence.models import chat_messages

    data, before, after, logs, receipts, _ = await run(db, text)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", 1)] and len(receipts) == 1
    assert after["version"] == before["version"] + 1
    searches = [log for log in logs if log["tool_name"] == "search_products"]
    assert searches
    assert all("qr" in log["input"]["filters"]["required_tags"] for log in searches)
    # The persisted plan carries the tag to the mutation-time guard, whose
    # REQUIRED_FEATURE_MISSING rejection is covered in test_mutations.py.
    async with db.connect() as conn:
        plan = await conn.scalar(sa.select(chat_messages.c.persisted_plan))
    adds = [step for step in plan if step["name"] == "add_to_quote"]
    assert len(adds) == 1 and "qr" in adds[0]["required_tags"]


async def test_semicolon_separated_adds_are_one_group(db):
    data, before, after, logs, receipts, _ = await run(
        db, "BlueScan Air 1 adet ekle; GreenScan Eco 1 adet ekle."
    )
    assert data["notice"] == ""
    assert sorted(items(after)) == [("PRD-BC-110", 1), ("PRD-BC-140", 1)]
    assert len(receipts) == 2
    assert after["version"] == before["version"] + 2  # one per applied mutation
    adds = [log for log in logs if log["tool_name"] == "add_to_quote"]
    assert [log["input"]["product_id"] for log in adds] == ["PRD-BC-110", "PRD-BC-140"]


# B07: an out-of-stock policy question is routed to the real stock policy.
@pytest.mark.parametrize(
    "text",
    [
        "Stokta olmayan ürünler için bekleme kuralı nedir?",
        "Stok dışı ürünlerde backorder politikası nasıl?",
    ],
)
async def test_out_of_stock_policy_question_cites_stock_rule(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert after == before and receipts == []
    assert not MUTATIONS & {log["tool_name"] for log in logs}
    entries = {
        e["knowledge_id"]
        for log in logs
        if log["tool_name"] == "get_knowledge_entries" and log["input"]["topic"] == "stock_rule"
        for e in log["output"]["entries"]
    }
    assert "KNE-STOCK-001" in entries
    assert entries <= {s["source_id"] for s in data["sources"] if s["kind"] == "knowledge"}
    assert data["notice"] == ""


# B09: history endpoints return the newest window, oldest first.
async def test_history_endpoints_return_latest_window(db):
    from datetime import UTC, datetime, timedelta

    from app.persistence.models import chat_messages

    app, client = await chat_client(db)
    async with app.router.lifespan_context(app), client:
        sid = await open_session(client, "Q-1002", "CUST-ANK-002")
        start = datetime.now(UTC) + timedelta(minutes=1)
        ids = [f"m{i:03d}" for i in range(205)]
        async with db.begin() as conn:
            await conn.execute(
                chat_messages.insert(),
                [
                    {
                        "session_id": sid,
                        "message_id": mid,
                        "body": mid,
                        "payload_hash": mid,
                        "status": "completed",
                        "created_at": start + timedelta(seconds=i),
                    }
                    for i, mid in enumerate(ids)
                ],
            )
            await conn.execute(
                tool_call_logs.insert(),
                [
                    {
                        "session_id": sid,
                        "message_id": ids[-1],
                        "attempt_id": "a",
                        "tool_sequence": n,
                        "tool_name": "get_quote",
                        "success": True,
                    }
                    for n in range(1, 506)
                ],
            )
        rows = (await client.get(f"/api/chat/sessions/{sid}/messages")).json()
        logs = (await client.get("/api/tool-calls", params={"session_id": sid})).json()
    assert [r["message_id"] for r in rows] == ids[-200:]
    assert [log["tool_sequence"] for log in logs] == list(range(6, 506))


# Re-audit R01/U02/U03: a limit's scope decides, not one keyword.
@pytest.mark.parametrize(
    "text,quote",
    [
        ("Hepsi için en fazla 9.000 TL, 2 adet BlueScan Air ekle.", "Q-1002"),
        ("Sepet tutarı 9.000 TL altında olsun, 2 adet BlueScan Air ekle.", "Q-1002"),
        ("İkisi birlikte 9.000 TL altında olsun, 2 adet BlueScan Air ekle.", "Q-1002"),
        ("Teklif tutarı 9.000 TL altında kalsın, BlueScan Air 1 adet ekle.", "Q-1002"),
        ("Bütçem 9.000 TL, BlueScan Air 1 adet ekle.", "Q-1002"),
        ("Bütçem 9.000 TL, BlueScan Air 1 adet daha ekle.", "Q-1001"),
        # A second limit without a currency word is still a second limit.
        ("BlueScan Air 8.500 TL altında 1 adet ekle; bütçem 5.000.", "Q-1002"),
    ],
)
async def test_total_or_ambiguous_budget_never_becomes_unit_ceiling(db, text, quote):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert_unchanged(data, before, after, logs, receipts)
    assert "değiştirmedim" in data["notice"]


@pytest.mark.parametrize(
    "text,quote,expected",
    [
        ("Birim bütçem 9.000 TL, 2 adet BlueScan Air ekle.", "Q-1002", 2),
        ("Adet başı 9.000 TL altında 2 adet BlueScan Air ekle.", "Q-1002", 2),
        ("Birim fiyatı 9.000 TL altında, BlueScan Air 1 adet daha ekle.", "Q-1001", 2),
        ("BlueScan Air birim fiyatı 8.500 TL altında 1 adet ekle; para birimi TRY.", "Q-1002", 1),
        ("BlueScan Air 8.500 TL altında 1 adet ekle; tavan yine 8500 TL.", "Q-1002", 1),
    ],
)
async def test_explicit_unit_limit_or_currency_note_still_adds(db, text, quote, expected):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", expected)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    adds = [log for log in logs if log["tool_name"] == "add_to_quote" and log["mutation_applied"]]
    assert len(adds) == 1


# Re-audit R02/U01: authority is decided per quoted span and per clause.
@pytest.mark.parametrize(
    "text",
    [
        "'BlueScan Air 1 adet ekle' ifadesini açıklar mısın?",
        "'BlueScan Air 1 adet ekle' yazarsam iade nasıl olur?",
        "`BlueScan Air 1 adet ekle` ne işe yarar?",
        "Önce benden onay al, sonra BlueScan Air 1 adet ekle.",
        "BlueScan Air 1 adet ekleyelim mi?",
        "BlueScan Air 1 adet ekle; GreenScan Eco ekleme.",
    ],
)
async def test_talked_about_or_mixed_command_explains_and_never_mutates(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)
    assert "değiştirmedim" in data["notice"]


@pytest.mark.parametrize(
    "text",
    [
        "Benden onay alındı, BlueScan Air 1 adet ekle.",
        'Örnekte "GreenScan Eco ekle" yazıyor. Şimdi BlueScan Air 1 adet ekle.',
        "Örnekte 'GreenScan Eco ekle' yazıyor. Şimdi BlueScan Air 1 adet ekle.",
        "BlueScan Air'i 1 adet ekle.",
        "'BlueScan Air' 1 adet ekle.",
        "BlueScan Air 1 adet ekler misin?",
    ],
)
async def test_granted_or_unquoted_command_adds_only_its_product(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert items(after) == [("PRD-BC-110", 1)], data["notice"]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    adds = [log["input"]["product_id"] for log in logs if log["tool_name"] == "add_to_quote"]
    assert adds == ["PRD-BC-110"]


# Re-audit R03: any stated-but-unparsed quantity form asks instead of guessing.
@pytest.mark.parametrize(
    "text",
    [
        "BlueScan Air ekle, adet: 2.",
        "BlueScan Air ekle, miktar=2.",
        "BlueScan Air ve GreenScan Eco 2'şer ekle.",
        "BlueScan Air ve GreenScan Eco ikişer adet ekle.",
        "BlueScan Air - 2 adet ekle.",
        "BlueScan Air 1 / 2 adet ekle.",
        "BlueScan Air 1/2 adet ekle.",
        "BlueScan Air 2 - 3 adet ekle.",
        "BlueScan Air bir buçuk adet ekle.",
    ],
)
async def test_unparsed_quantity_form_never_mutates(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)


@pytest.mark.parametrize(
    "text,quantity",
    [("BlueScan Air tek adet ekle.", 1), ("BlueScan Air ２ adet ekle.", 2)],
)
async def test_supported_quantity_forms_still_add(db, text, quantity):
    data, before, after, _, receipts, _ = await run(db, text)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-110", quantity)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1


# Re-audit R04: a target feature binds the target even when the source has it too.
@pytest.mark.parametrize(
    "text,quote",
    [
        ("BlueScan Air ürününü QR'lı GreenScan Eco ile değiştir.", "Q-1001"),
        ("BlueScan Pro ürününü 2D GreenScan Eco ile değiştir.", "Q-1004"),
        ("Kablosuz okuyucuyu QR'lı GreenScan Eco ile değiştir.", "Q-1001"),
        ("GreenScan Eco ile BlueScan Pro'yu değiştir; 2D zorunlu.", "Q-1004"),
    ],
)
async def test_target_feature_is_never_dropped(db, text, quote):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert_unchanged(data, before, after, logs, receipts)


@pytest.mark.parametrize(
    "text,quote",
    [
        ("QR'lı BlueScan Air ürününü GreenScan Eco ile değiştir.", "Q-1001"),
        ("2D BlueScan Pro'yu GreenScan Eco ile değiştir.", "Q-1004"),
        ("Kablosuz okuyucuyu GreenScan Eco ile değiştir.", "Q-1001"),
        ("BlueScan Air ürününü kablosuz GreenScan Eco ile değiştir.", "Q-1001"),
    ],
)
async def test_source_feature_does_not_bind_target(db, text, quote):
    data, before, after, logs, receipts, _ = await run(db, text, quote)
    assert data["notice"] == ""
    assert items(after) == [("PRD-BC-140", 1)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    replaces = [log for log in logs if log["tool_name"] == "replace_with_alternative"]
    assert [r["input"]["to_product_id"] for r in replaces] == ["PRD-BC-140"]


# Re-audit R05/R06: every clause keeps its scope.
@pytest.mark.parametrize(
    "text",
    [
        "QR zorunlu; BlueScan Lite 1 adet ekle.",
        "QR zorunlu; BlueScan Air ve BlueScan Lite 1 adet ekle.",
        "BlueScan Air hakkında; GreenScan Eco 1 adet ekle.",
        "BlueScan Air 1 adet ekle ve GreenScan Eco'nun fiyatı ne?",
        "GreenScan Eco kaç TL ve BlueScan Air 1 adet ekle.",
        "BlueScan Air 1 adet ekle ve GreenScan Eco fiyatını göster.",
    ],
)
async def test_leading_feature_or_question_clause_never_mutates(db, text):
    data, before, after, logs, receipts, _ = await run(db, text)
    assert_unchanged(data, before, after, logs, receipts)


# Re-audit R07: stock-out questions cite the stock policy; a named product is still looked up.
async def test_stock_out_question_about_named_product_cites_policy_and_product(db):
    data, before, after, logs, receipts, _ = await run(db, "BlueScan Air stokta yok mu?")
    assert after == before and receipts == []
    assert not MUTATIONS & {log["tool_name"] for log in logs}
    assert "PRD-BC-110" in data["recommended_product_ids"]
    cited = {s["source_id"] for s in data["sources"] if s["kind"] == "knowledge"}
    assert "KNE-STOCK-001" in cited
