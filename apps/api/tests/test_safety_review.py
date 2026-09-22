"""Video review regressions: intent, grounded reads, and real persisted effects."""

from decimal import Decimal

import pytest
import sqlalchemy as sa

from app.persistence.models import chat_messages, mutation_receipts, quote_items, tool_call_logs
from tests.test_chat import chat_client, message, open_session


async def exchange(db, text, *, eligible=True, retry=False):
    quote = "Q-1002" if eligible else "Q-1001"
    customer = "CUST-ANK-002" if eligible else "CUST-IST-001"
    app, client = await chat_client(db)
    async with app.router.lifespan_context(app), client:
        sid = await open_session(client, quote, customer)
        before = (await client.get(f"/api/quotes/{quote}")).json()
        async with db.connect() as conn:
            original_rows = (
                (await conn.execute(sa.select(quote_items).order_by(quote_items.c.quote_item_id)))
                .mappings()
                .all()
            )
        payload = message(sid, text, quote)
        response = await client.post("/api/chat", json=payload)
        assert response.status_code == 200, response.text
        first = (await client.get(f"/api/quotes/{quote}")).json()
        if retry:
            repeated = await client.post("/api/chat", json=payload)
            assert repeated.status_code == 200, repeated.text
            assert (await client.get(f"/api/quotes/{quote}")).json() == first
    async with db.connect() as conn:
        logs = (
            (await conn.execute(sa.select(tool_call_logs).order_by(tool_call_logs.c.log_id)))
            .mappings()
            .all()
        )
        receipts = (await conn.execute(sa.select(mutation_receipts))).mappings().all()
        stored = (await conn.execute(sa.select(chat_messages))).mappings().one()
        final_rows = (
            (await conn.execute(sa.select(quote_items).order_by(quote_items.c.quote_item_id)))
            .mappings()
            .all()
        )
    return response.json(), before, first, logs, receipts, stored, original_rows, final_rows


CEILINGS = [
    ("8.500'e kadar", None),
    ("8.500'den ucuz", None),
    ("8.500 TL'ye kadar", "8500"),
    ("8.500 TL üstü olmayan", None),
    ("8.500 TL altında", "8500"),
    ("8.500 TL altı", "8500"),
    ("8.500 TL'den ucuz", "8500"),
    ("8.500 lirayı geçmeyen", None),
    ("₺8.500 altında", None),
    ("8.500 ₺ altında", None),
    ("8 bin TL altında", None),
    ("8 bin altında", None),
]


@pytest.mark.parametrize("ceiling,parsed", CEILINGS)
@pytest.mark.parametrize("action", ["öner", "ekle"])
async def test_ceiling_never_disappears_from_read_or_write(db, ceiling, parsed, action):
    data, before, after, logs, receipts, stored, rows, final = await exchange(
        db, f"{ceiling} BlueScan Pro barkod okuyucu {action}."
    )
    assert after == before and final == rows
    assert receipts == []
    assert not {"add_to_quote", "update_quote_item", "replace_with_alternative"} & {
        log["tool_name"] for log in logs
    }
    assert data["recommended_product_ids"] == []  # Explicit Pro costs 12,950, above every ceiling.
    searches = [log for log in logs if log["tool_name"] == "search_products"]
    if parsed is None:
        assert searches == []
        assert "Fiyat sınırını kesinleştiremedim" in data["notice"]
    else:
        assert searches
        assert Decimal(stored["trusted_constraints"]["max_price_try"]) == Decimal(parsed)
        for log in searches:
            assert Decimal(log["input"]["filters"]["max_price_try"]) == Decimal(parsed)
            assert all(
                Decimal(p["price_try"]) <= Decimal(parsed) for p in log["output"]["recommendations"]
            )


@pytest.mark.parametrize("text", ["BlueScan Air kaç TL?", "3 adet BlueScan Air fiyatı"])
async def test_price_information_is_not_a_ceiling_or_mutation(db, text):
    data, before, after, logs, receipts, stored, rows, final = await exchange(db, text)
    assert data["recommended_product_ids"] == ["PRD-BC-110"]
    assert "7990.00 TL" in data["text"]
    assert data["notice"] == ""
    assert after == before and final == rows and receipts == []
    assert stored["trusted_constraints"]["max_price_try"] is None
    searches = [log for log in logs if log["tool_name"] == "search_products"]
    assert len(searches) == 1 and searches[0]["input"]["filters"]["max_price_try"] is None


async def test_valid_ceiling_still_recommends_and_adds_affordable_product(db):
    data, before, after, logs, receipts, _, _, _ = await exchange(
        db, "8.500 TL altında BlueScan Air 1 adet ekler misin?", retry=True
    )
    assert data["recommended_product_ids"] == ["PRD-BC-110"]
    assert [(p["product_id"], p["quantity"]) for p in after["items"]] == [("PRD-BC-110", 1)]
    assert after["version"] == before["version"] + 1 and len(receipts) == 1
    mutations = [log for log in logs if log["tool_name"] == "add_to_quote"]
    assert [(m["mutation_applied"], m["replayed"]) for m in mutations] == [
        (True, False),
        (False, True),
    ]


@pytest.mark.parametrize(
    "ceiling,expected",
    [("7.989,99", []), ("7.990", ["PRD-BC-110"]), ("7.990,01", ["PRD-BC-110"])],
)
async def test_ceiling_boundary_uses_catalog_unit_price(db, ceiling, expected):
    data, before, after, logs, receipts, _, rows, final = await exchange(
        db, f"{ceiling} TL altı BlueScan Air öner."
    )
    assert data["recommended_product_ids"] == expected
    assert after == before and final == rows and receipts == []
    assert "add_to_quote" not in [log["tool_name"] for log in logs]


@pytest.mark.parametrize(
    "consent",
    [
        "bekleyebilirim demiyorum",
        "bekleyebilirim demedim",
        "bekleyebilirim diyemem",
        "bekleyebilirim değil",
        "bekleyebilirim ama beklemek istemiyorum",
        "bekleyebilirim mi?",
        "bir haftada gelirse bekleyebilirim",
        '"bekleyebilirim"',
        '"bekleyebilirim."',
        "bekleyebilirim, demiyorum",
        "bekleyebilirim, ama bir haftada gelmeli",
        "",
    ],
)
async def test_uncertain_backorder_never_creates_receipt(db, consent):
    data, before, after, logs, receipts, stored, rows, final = await exchange(
        db, f"PRD-BC-130 1 adet ekle, {consent}."
    )
    assert stored["trusted_constraints"]["explicit_backorder_consent"] is False
    assert after == before and final == rows and receipts == []
    assert "add_to_quote" not in [log["tool_name"] for log in logs]
    assert "PRD-BC-130" not in data["recommended_product_ids"]


@pytest.mark.parametrize(
    "text",
    [
        "PRD-BC-130 1 adet ekle, bekleyebilirim.",
        "PRD-BC-130 1 adet ekle; beklemeyi kabul ediyorum.",
        "PRD-BC-130 1 adet ekle, backorder kabul ediyorum.",
        "PRD-BC-130 1 adet ekler misin? Bekleyebilirim.",
        "Bekleyebilirim; PRD-BC-130 1 adet ekle.",
    ],
)
@pytest.mark.parametrize("eligible", [False, True])
async def test_affirmative_backorder_requires_customer_and_replays_once(db, text, eligible):
    _, before, after, logs, receipts, stored, rows, final = await exchange(
        db, text, eligible=eligible, retry=True
    )
    assert stored["trusted_constraints"]["explicit_backorder_consent"] is True
    mutations = [log for log in logs if log["tool_name"] == "add_to_quote"]
    if eligible:
        assert [
            (p["product_id"], p["quantity"], p["fulfillment_status"]) for p in after["items"]
        ] == [("PRD-BC-130", 1, "backorder")]
        assert after["version"] == before["version"] + 1 and len(receipts) == 1
        assert [(m["mutation_applied"], m["replayed"]) for m in mutations] == [
            (True, False),
            (False, True),
        ]
    else:
        assert after == before and final == rows and receipts == [] and mutations == []


@pytest.mark.parametrize(
    "text",
    [
        "Starter lisansı offline çalışır mı?",
        "Starter lisansı çevrimdışı çalışır mı?",
        "Starter şube senkronu destekler mi?",
    ],
)
async def test_compatibility_question_answers_from_real_knowledge_without_writes(db, text):
    data, before, after, logs, receipts, _, rows, final = await exchange(db, text)
    ids = {s["source_id"] for s in data["sources"] if s["kind"] == "knowledge"}
    assert {"KNE-COMP-001", "KNE-COMP-001-SUP"} <= ids
    assert "Starter lisans offline senkron içermez" in data["text"]
    assert data["recommended_product_ids"] == []
    assert after == before and final == rows and receipts == []
    comp = [
        log
        for log in logs
        if log["tool_name"] == "get_knowledge_entries" and log["input"]["topic"] == "compatibility"
    ]
    assert len(comp) == 1
    assert {e["knowledge_id"] for e in comp[0]["output"]["entries"]} == {
        "KNE-COMP-001",
        "KNE-COMP-001-SUP",
    }


@pytest.mark.parametrize(
    "text,expected",
    [
        ("BlueScan Air kaç TL?", False),
        ("3 adet BlueScan Air fiyatı", False),
        ("Şimdiye kadar eklediğime 1 tane daha ekle", False),
        ("8.500 TL altı", True),
        ("8.500 TL'den ucuz", True),
        ("8 bin altında", True),
        ("₺8.500", True),
        ("Bütçem sınırlı", True),
    ],
)
def test_ceiling_intent_distinguishes_information(text, expected):
    from app.services.normalization import has_price_ceiling_intent

    assert has_price_ceiling_intent(text) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("bekleyebilirim", True),
        ("Beklemeyi kabul ediyorum.", True),
        ("bekleyebilirim demiyorum", False),
        ("bekleyebilirim mi?", False),
        ("gelirse bekleyebilirim", False),
        ('"bekleyebilirim"', False),
        ('"bekleyebilirim."', False),
        ("bekleyebilirim, ama hemen gelmeli", False),
        ("Ekler misin? Bekleyebilirim.", True),
        ("bekleyebilirim, demedim", False),
    ],
)
def test_backorder_consent_is_an_affirmative_statement(text, expected):
    from app.services.normalization import has_backorder_consent

    assert has_backorder_consent(text) is expected


NON_MONETARY_READS = [
    ("Yarına kadar 2 adet okuyucu teslim edilir mi?", "delivery_policy"),
    ("3 güne kadar teslim olur mu?", "delivery_policy"),
    ("Garanti 24 aya kadar mı?", "warranty"),
    ("En ucuz 2D okuyucu hangisi?", None),
    ("3 tane ucuz okuyucu öner.", None),
]


@pytest.mark.parametrize("text,topic", NON_MONETARY_READS)
async def test_non_monetary_read_has_no_ceiling_or_mutation(db, text, topic):
    data, before, after, logs, receipts, stored, rows, final = await exchange(db, text)
    assert data["notice"] == ""
    assert after == before and final == rows and receipts == []
    assert stored["trusted_constraints"]["max_price_try"] is None
    assert not {"add_to_quote", "update_quote_item", "replace_with_alternative"} & {
        log["tool_name"] for log in logs
    }
    if topic:
        entries = [
            entry
            for log in logs
            if log["tool_name"] == "get_knowledge_entries" and log["input"]["topic"] == topic
            for entry in log["output"]["entries"]
        ]
        assert entries
        ids = {s["source_id"] for s in data["sources"] if s["kind"] == "knowledge"}
        assert {entry["knowledge_id"] for entry in entries} <= ids
    else:
        searches = [log for log in logs if log["tool_name"] == "search_products"]
        assert searches and data["recommended_product_ids"]
        assert all(log["input"]["filters"]["max_price_try"] is None for log in searches)


@pytest.mark.parametrize(
    "text,expected",
    [
        *[(text, False) for text, _ in NON_MONETARY_READS],
        *[(f"{ceiling} okuyucu öner.", True) for ceiling, _ in CEILINGS],
        ("En ucuz 4G terminal hangisi?", False),
        ("En ucuz Model80 hangisi?", False),
        ("En ucuz 80 mm yazıcı hangisi?", False),
        ("2 haftaya kadar teslim edilir mi?", False),
        ("48 saate kadar teslim olur mu?", False),
        ("3 lisans ucuz olur mu?", False),
        ("2D kadar ucuz okuyucu öner.", False),
        ("8500’e kadar okuyucu öner.", True),
        ("9000den ucuz okuyucu öner.", True),
        ("Altı adet BlueScan Air ekle.", True),
    ],
)
def test_ceiling_marker_requires_adjacent_amount(text, expected):
    from app.services.normalization import has_price_ceiling_intent

    assert has_price_ceiling_intent(text) is expected


async def test_written_six_never_defaults_to_one(db):
    data, before, after, logs, receipts, _, rows, final = await exchange(
        db, "Altı adet BlueScan Air ekle."
    )
    assert after == before and final == rows and receipts == []
    assert "değiştirmedim" in data["notice"]
    assert not {"add_to_quote", "update_quote_item", "replace_with_alternative"} & {
        log["tool_name"] for log in logs
    }


BIN_CEILINGS = [
    "8 bine kadar",
    "8 bin liraya kadar",
    "8 bin TL'ye kadar",
    "10 bin liradan ucuz",
    "on bin liraya kadar",
    "8 bin TL civarı",
    "8 bin ₺ civarı",
    "yüz bin liraya kadar",
    "sekiz bine kadar",
    "8 bin TRY kadar",
]


@pytest.mark.parametrize("ceiling", BIN_CEILINGS)
@pytest.mark.parametrize("action", ["öner", "ekle"])
async def test_bin_ceiling_never_becomes_unbounded_search(db, ceiling, action):
    data, before, after, logs, receipts, stored, rows, final = await exchange(
        db, f"{ceiling} endüstriyel barkod okuyucu {action}."
    )
    assert "Fiyat sınırını kesinleştiremedim" in data["notice"]
    assert data["recommended_product_ids"] == []
    assert after == before and final == rows and receipts == []
    assert stored["trusted_constraints"]["max_price_try"] is None
    assert not {
        "search_products",
        "add_to_quote",
        "update_quote_item",
        "replace_with_alternative",
    } & {log["tool_name"] for log in logs}


@pytest.mark.parametrize("ceiling", BIN_CEILINGS)
def test_bin_money_expression_has_ceiling_intent(ceiling):
    from app.services.normalization import has_price_ceiling_intent

    assert has_price_ceiling_intent(f"{ceiling} okuyucu öner.") is True


@pytest.mark.parametrize(
    "text",
    [
        "8 bin adede kadar teslim olur mu?",
        "On güne kadar teslim olur mu?",
        "Yüz lisans ucuz olur mu?",
        "En ucuz BIN8 okuyucu hangisi?",
        "Garanti iki yıla kadar mı?",
    ],
)
def test_written_number_with_non_money_unit_is_not_ceiling(text):
    from app.services.normalization import has_price_ceiling_intent

    assert has_price_ceiling_intent(text) is False
