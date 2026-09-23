"""Independent re-audit variant matrix (reports/reaudit_20260923_variant_matrix.json) as HTTP/DB tests.

Each case runs on a fresh migrated+seeded PostgreSQL DB through /api/chat. NO_CHANGE means the
canonical quote, version, receipts and mutation logs stay untouched; a dict is the exact active
item set afterwards; safe(...) accepts either the listed items or an unchanged quote.
"""

import pytest
import sqlalchemy as sa

from app.persistence.models import mutation_receipts, tool_call_logs
from tests.test_chat import chat_client, message, open_session

NO_CHANGE = "no_change"
MUTATIONS = {"add_to_quote", "update_quote_item", "replace_with_alternative"}
CUSTOMERS = {
    "Q-1001": "CUST-IST-001",
    "Q-1002": "CUST-ANK-002",
    "Q-1004": "CUST-IST-001",
    "Q-2001": "CUST-EXT-001",
    "Q-2003": "CUST-EXT-003",
}
# Read-only policy questions must cite the real knowledge topic, not only fallback sources.
POLICY_TOPIC = {
    "Stokta yoksa bekleme koşulları nedir?": "stock_rule",
    "Stoksuz ürün için sipariş politikası nedir?": "stock_rule",
    "Stoğu biten ürünü bekleyebilir miyim?": "stock_rule",
    "Backorder nasıl çalışır?": "stock_rule",
    "Bekleme için izin koşulları nedir?": "stock_rule",
    "Stok dışı ürünlerin bekleme politikası nedir?": "stock_rule",
    "Stokta olan donanımlar için teslimat kuralı nedir?": "delivery_policy",
    "Stokta olan ürünler ne zaman sevk edilir?": "delivery_policy",
}


def safe(items):
    return ("safe", items)


CASES = [
    ('B03', 'Q-1002', "'BlueScan Air 1 adet ekle' ifadesini açıklar mısın?", NO_CHANGE, ()),
    ('B03', 'Q-1002', "'BlueScan Air 1 adet ekle' yazarsam iade nasıl olur?", NO_CHANGE, ()),
    ('B03', 'Q-1002', '"BlueScan Air 1 adet ekle" ifadesini açıklar mısın?', NO_CHANGE, ()),
    ('B03', 'Q-1002', "'BlueScan Air' 1 adet ekle.", {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'BlueScan Air 1 adet ekleyelim mi?', NO_CHANGE, ()),
    ('B03', 'Q-1002', 'BlueScan Air 1 adet eklesem mi?', NO_CHANGE, ()),
    ('B03', 'Q-1002', 'Onay verdim, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'Onaylıyorum, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'Onay almadan BlueScan Air 1 adet ekleme.', NO_CHANGE, ()),
    ('B03', 'Q-1002', 'BlueScan Air 1 adet ekler misin?', {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'Örnekte "GreenScan Eco ekle" yazıyor. Şimdi BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'Benden onay alındı, BlueScan Air 1 adet ekle.', {'PRD-BC-110': 1}, ()),
    ('B03', 'Q-1002', 'Diyelim ki BlueScan Air 1 adet ekle dedim, ne olur?', NO_CHANGE, ()),
    ('B03', 'Q-1002', '"BlueScan Air" 1 adet ekler misin?', {'PRD-BC-110': 1}, ()),
    ('B06', 'Q-1002', 'BlueScan Air on iki adet ekle.', NO_CHANGE, ()),
    ('B06', 'Q-1002', 'BlueScan Air tek adet ekle.', {'PRD-BC-110': 1}, ()),
    ('B06', 'Q-1002', 'BlueScan Air 1 adet ve GreenScan Eco iki adet ekle.', NO_CHANGE, ()),
    ('B06', 'Q-1002', 'BlueScan Air ekle, adet: 2.', safe({'PRD-BC-110': 2}), ()),
    ('B06', 'Q-1002', "BlueScan Air ve GreenScan Eco 2'şer ekle.", safe({'PRD-BC-110': 2, 'PRD-BC-140': 2}), ()),
    ('B06', 'Q-1002', 'BlueScan Air ２ adet ekle.', {'PRD-BC-110': 2}, ()),
    ('B06', 'Q-1001', 'BlueScan Air miktarını iki adede güncelle.', NO_CHANGE, ()),
    ('B06', 'Q-1001', 'BlueScan Air miktarını güncelle, adet: 2.', safe({'PRD-BC-110': 2}), ()),
    ('B06', 'Q-1001', 'BlueScan Air iki tane daha ekle.', NO_CHANGE, ()),
    ('B06', 'Q-1001', 'BlueScan Air 1 adet daha ekle.', {'PRD-BC-110': 2}, ()),
    ('B06', 'Q-1001', 'BlueScan Air toplam iki adet olsun.', NO_CHANGE, ()),
    ('B06', 'Q-1001', 'BlueScan Air toplam 4 adet olsun.', {'PRD-BC-110': 4}, ()),
    ('B06', 'Q-1001', 'BlueScan Air miktarını −2 adede güncelle.', NO_CHANGE, ()),
    ('B06', 'Q-1002', 'BlueScan Air - 2 adet ekle.', NO_CHANGE, ()),
    ('B06', 'Q-1002', 'BlueScan Air 1 / 2 adet ekle.', NO_CHANGE, ()),
    ('B01', 'Q-1002', 'BlueScan Air 8.500 TL altında 1 adet ekle; bütçem 5.000 TRY.', NO_CHANGE, ()),
    ('B01', 'Q-1002', 'En fazla 5.000 TRY olsun; BlueScan Air 8.500 TL altında 1 adet ekle.', NO_CHANGE, ()),
    ('B01', 'Q-1002', 'BlueScan Air 8.500 TL altında 1 adet ekle; en fazla ₺5.000.', NO_CHANGE, ()),
    ('B01', 'Q-1002', 'BlueScan Air 8.500 TL altında 1 adet ekle; tavan 5.000 TL.', NO_CHANGE, ()),
    ('B01', 'Q-1002', 'BlueScan Air 8.500 TL altında 1 adet ekle; tavan yine 8500 TL.', safe({'PRD-BC-110': 1}), ()),
    ('B01', 'Q-1002', 'BlueScan Air birim fiyatı 8.500 TL altında 1 adet ekle; GreenScan Eco kaç TL?', safe({'PRD-BC-110': 1}), ()),
    ('B01', 'Q-1002', 'BlueScan Air birim fiyatı 8.500 TL altında 1 adet ekle; para birimi TRY.', {'PRD-BC-110': 1}, ()),
    ('B02', 'Q-1001', 'Bütçem 9.000 TL, BlueScan Air 1 adet daha ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1001', 'Sepet tutarı 9.000 TL altında kalsın, BlueScan Air 1 adet daha ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1002', 'Toplamda 9.000 TL altında 2 adet BlueScan Air ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1002', 'Hepsi için en fazla 9.000 TL, 2 adet BlueScan Air ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1002', 'Tamamı 9.000 TL altında olacak şekilde 2 adet BlueScan Air ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1002', 'Sepet tutarı 9.000 TL altında olsun, 2 adet BlueScan Air ekle.', NO_CHANGE, ()),
    ('B02', 'Q-1001', 'BlueScan Air toplam 4 adet olsun, birim fiyatı 9.000 TL altında.', {'PRD-BC-110': 4}, ()),
    ('B02', 'Q-1002', 'Birim bütçem 9.000 TL, 2 adet BlueScan Air ekle.', {'PRD-BC-110': 2}, ()),
    ('B02', 'Q-1001', 'Teklifin toplamı 9.000 TL altında kalsın, BlueScan Air 1 adet daha ekle.', NO_CHANGE, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü GreenScan Eco ile değiştir.', {'PRD-BC-140': 3}, ('GreenScan Eco 2 adet ekle.',)),
    ('B04', 'Q-1004', "GreenScan Eco ile BlueScan Pro'yu değiştir.", {'PRD-BC-140': 3}, ('GreenScan Eco 2 adet ekle.',)),
    ('B04', 'Q-1004', "BlueScan Pro'yu değiştir, yerine GreenScan Eco ekle.", {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', 'BlueScan Pro yerine GreenScan Eco ekle.', safe({'PRD-BC-140': 1}), ()),
    ('B04', 'Q-2001', 'BlueScan Air Plus ürününü GreenScan Eco Plus ile değiştir.', {'PRD-BC-140-PLUS': 1}, ()),
    ('B04', 'Q-1004', 'PRD-BC-120 ürününü GreenScan Eco ile değiştir.', {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü PRD-BC-140 ile değiştir.', {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', "BlueScan Pro ürününü QR'lı GreenScan Eco ile değiştir.", NO_CHANGE, ()),
    ('B04', 'Q-1001', "BlueScan Air ürününü QR'lı GreenScan Eco ile değiştir.", NO_CHANGE, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü 2D GreenScan Eco ile değiştir.', NO_CHANGE, ()),
    ('B04', 'Q-1004', "2D BlueScan Pro'yu GreenScan Eco ile değiştir.", {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü stoklu GreenScan Eco ile değiştir.', {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü değiştir; GreenScan Eco olsun.', {'PRD-BC-140': 1}, ()),
    ('B04', 'Q-1004', 'BlueScan Pro ürününü BlueScan Lite ile değiştir.', NO_CHANGE, ()),
    ('B04', 'Q-1001', 'BlueScan Air ürününü GreenScan Eco ile değiştir; QR zorunlu.', NO_CHANGE, ()),
    ('B04', 'Q-1001', "QR'lı BlueScan Air ürününü GreenScan Eco ile değiştir.", {'PRD-BC-140': 1}, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; kablosuz olmasın.', NO_CHANGE, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; GreenScan Eco ekleme.', NO_CHANGE, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; QR zorunlu.', {'PRD-BC-110': 1}, ()),
    ('B05', 'Q-1002', 'BlueScan Lite 1 adet ekle; QR zorunlu.', NO_CHANGE, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; GreenScan Eco 1 adet ekle.', {'PRD-BC-110': 1, 'PRD-BC-140': 1}, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; GreenScan Eco.', NO_CHANGE, ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; GreenScan Eco için fiyat bilgisi istiyorum.', safe({'PRD-BC-110': 1}), ()),
    ('B05', 'Q-1002', 'BlueScan Air 1 adet ekle; not: müşteri öğleden sonra gelecek.', {'PRD-BC-110': 1}, ()),
    ('B05', 'Q-1002', 'BlueScan Lite 1 adet ekle ve QR zorunlu.', NO_CHANGE, ()),
    ('B05', 'Q-1002', 'BlueScan Air ve GreenScan Eco 1 adet ekle.', {'PRD-BC-110': 1, 'PRD-BC-140': 1}, ()),
    ('B05', 'Q-1002', "BlueScan Air 1 adet ekle ve GreenScan Eco'nun fiyatı ne?", safe({'PRD-BC-110': 1}), ()),
    ('B05', 'Q-1002', 'QR zorunlu; BlueScan Lite 1 adet ekle.', NO_CHANGE, ()),
    ('B05', 'Q-1002', "Sahada internet yok; 4G'li el terminali ve offline senkron için gereken lisansı ekle.", {'PRD-POS-210': 1, 'PRD-SW-520': 1}, ()),
    ('B05', 'Q-1002', '3 adet BlueScan Air ekle; partner indirimini de açıkla.', {'PRD-BC-110': 3}, ()),
    ('B07', 'Q-1002', 'Stokta yoksa bekleme koşulları nedir?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Stoksuz ürün için sipariş politikası nedir?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Stoğu biten ürünü bekleyebilir miyim?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Backorder nasıl çalışır?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Bekleme için izin koşulları nedir?', NO_CHANGE, ()),
    ('B07', 'Q-2003', 'Stokta olan donanımlar için teslimat kuralı nedir?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Stokta olan ürünler ne zaman sevk edilir?', NO_CHANGE, ()),
    ('B07', 'Q-1002', 'Stok dışı ürünlerin bekleme politikası nedir?', NO_CHANGE, ()),
]


# Price-limit refusals must not recommend the over-limit product either (auditor's oracle).
NO_RECOMMENDATIONS = {
    "BlueScan Air 8.500 TL altında 1 adet ekle; bütçem 5.000 TRY.",
    "En fazla 5.000 TRY olsun; BlueScan Air 8.500 TL altında 1 adet ekle.",
    "BlueScan Air 8.500 TL altında 1 adet ekle; en fazla ₺5.000.",
    "BlueScan Air 8.500 TL altında 1 adet ekle; tavan 5.000 TL.",
}


async def check_variant(
    db,
    quote,
    text,
    expected,
    preludes=(),
    *,
    topic=None,
    knowledge=None,
    no_recommendations=False,
    read=False,
    recommendations=None,
):
    app, client = await chat_client(db)
    async with app.router.lifespan_context(app), client:
        sid = await open_session(client, quote, CUSTOMERS[quote])
        for prelude in preludes:
            setup = await client.post("/api/chat", json=message(sid, prelude, quote))
            assert setup.status_code == 200, setup.text
        before = (await client.get(f"/api/quotes/{quote}")).json()
        async with db.connect() as conn:
            receipts_before = await conn.scalar(
                sa.select(sa.func.count()).select_from(mutation_receipts)
            )
        request = message(sid, text, quote)
        response = await client.post("/api/chat", json=request)
        assert response.status_code == 200, response.text
        after = (await client.get(f"/api/quotes/{quote}")).json()
    async with db.connect() as conn:
        receipts_after = await conn.scalar(
            sa.select(sa.func.count()).select_from(mutation_receipts)
        )
        logs = (
            (
                await conn.execute(
                    sa.select(tool_call_logs).where(
                        tool_call_logs.c.message_id == request["message_id"]
                    )
                )
            )
            .mappings()
            .all()
        )
    body = response.json()
    attempted = [log["tool_name"] for log in logs if log["tool_name"] in MUTATIONS]
    applied = [log for log in logs if log["tool_name"] in MUTATIONS and log["mutation_applied"]]
    receipts = receipts_after - receipts_before
    unchanged = after == before and receipts == 0 and not applied
    items = {p["product_id"]: p["quantity"] for p in after["items"]}
    if expected == NO_CHANGE:
        assert unchanged, (items, body["notice"])
        # The planner itself refuses; a refusal must not depend on an executor guard.
        assert not attempted, (attempted, body["notice"])
        assert body["notice"] or topic or knowledge or read
    elif isinstance(expected, tuple):
        assert (unchanged and not attempted) or items == expected[1], (items, body["notice"])
    else:
        assert items == expected and not unchanged, (items, body["notice"])
    if not unchanged:
        # One receipt and one quote version per applied mutation, nothing else.
        assert applied and receipts == len(applied) == after["version"] - before["version"]
    if no_recommendations:
        assert body["recommended_product_ids"] == [], body["recommended_product_ids"]
    if recommendations is not None:
        assert body["recommended_product_ids"] == recommendations, body["recommended_product_ids"]
    if topic:
        entries = {
            e["knowledge_id"]
            for log in logs
            if log["tool_name"] == "get_knowledge_entries" and log["input"]["topic"] == topic
            for e in log["output"]["entries"]
        }
        assert entries
        cited = {s["source_id"] for s in body["sources"] if s["kind"] == "knowledge"}
        assert entries <= cited
    # A safe(...) case may answer with a clarification; its source oracle is for the change.
    if knowledge and not (isinstance(expected, tuple) and unchanged):
        assert knowledge in {s["source_id"] for s in body["sources"] if s["kind"] == "knowledge"}


@pytest.mark.parametrize(
    "group,quote,text,expected,preludes", CASES, ids=[f"{c[0]}-{i:02d}" for i, c in enumerate(CASES)]
)
async def test_reaudit_variant(db, group, quote, text, expected, preludes):
    await check_variant(
        db,
        quote,
        text,
        expected,
        preludes,
        topic=POLICY_TOPIC.get(text),
        no_recommendations=text in NO_RECOMMENDATIONS,
    )
