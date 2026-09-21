"""Read-only company scenarios enter the same HTTP chat route as clients.

The assertion registry interprets Turkish quote_assertion text, never runtime routing.
"""

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import sqlalchemy as sa

from app.main import create_app
from app.persistence.models import products, quote_items, tool_call_logs
from app.persistence.seed import seed_database

SOURCE = Path("/app/test-source/golden_test_scenarios.json")
if not SOURCE.exists():
    SOURCE = Path(__file__).resolve().parents[5] / "data/source/golden_test_scenarios.json"
SCENARIOS = json.loads(SOURCE.read_text())
# Expected final changed products (not inferred from the implementation's results).
EXPECTED = {
    "SCN-001": {"PRD-BC-110": 1},
    "SCN-003": {"PRD-BC-110": 3},
    "SCN-004": {"PRD-PRN-320": 4},
    "SCN-005": {"PRD-BC-120": None, "PRD-BC-110": 1},
    "SCN-006": {"PRD-BC-130": None, "PRD-BC-140": 2},
    "SCN-008": {"PRD-POS-210": 1, "PRD-SW-520": 1},
    "SCN-010": {"PRD-BC-110": 2},
    "SCN-011": {"PRD-BC-110": 3},
    "SCN-012": {"PRD-ACC-710": 1},
    "SCN-013": {"PRD-BC-110-PLUS": 2},
    "SCN-014": {"PRD-PRN-330": None, "PRD-PRN-320": 1},
    "SCN-015": {"PRD-SVC-810": 2},
    "SCN-017": {"PRD-SW-520": 1, "PRD-SW-530": 1},
    "SCN-019": {"PRD-BC-110-PLUS": 4},
    "SCN-020": {"PRD-BC-110": 1},
    "SCN-022": {"PRD-ACC-740": 1},
}
NET = {"SCN-011": "22292.10", "SCN-017": "22816.00", "SCN-019": "35456.80"}
MUTATIONS = {"add_to_quote", "update_quote_item", "replace_with_alternative"}


def matches(expected, row, logs):
    if row["tool_name"] != expected["name"]:
        return False
    for key, value in expected.get("must_match", {}).items():
        actual = row["input"]
        if key == "query_contains":
            if value.casefold() not in actual.get("query", "").casefold():
                return False
        elif key == "same_idempotency_key":
            previous = [
                r
                for r in logs
                if r["log_id"] < row["log_id"] and r["tool_name"] == row["tool_name"]
            ]
            if not previous or actual["idempotency_key"] != previous[0]["input"]["idempotency_key"]:
                return False
        elif key == "replayed":
            if row["replayed"] is not value or row["mutation_applied"]:
                return False
        elif key in {"max_price_try", "in_stock_only", "required_tags"}:
            actual = actual["filters"].get(key)
            if key == "max_price_try":
                if actual is None or Decimal(actual) != Decimal(value):
                    return False
            elif actual != value:
                return False
        elif actual.get(key) != value:
            return False
    return True


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["scenario_id"])
async def test_golden_message_through_http(db, monkeypatch, scenario, request):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("LLM_MODE", "off")
    evidence = request.node.golden_evidence
    evidence["database"] = db.url.database
    await seed_database(db)
    app = create_app(db)
    async with db.connect() as conn:
        original_rows = (
            (await conn.execute(sa.select(quote_items).order_by(quote_items.c.quote_item_id)))
            .mappings()
            .all()
        )
        original_stock = (
            await conn.execute(
                sa.select(products.c.product_id, products.c.stock_qty).order_by(
                    products.c.product_id
                )
            )
        ).all()
    evidence["before_rows"] = [dict(r) for r in original_rows]
    evidence["before_stock"] = [dict(r._mapping) for r in original_stock]
    quote_id = scenario["quote_id"]
    before = {
        r["product_id"]: r["quantity"]
        for r in original_rows
        if r["quote_id"] == quote_id and r["status"] == "active"
    }
    expected_final = dict(before)
    for product, quantity in EXPECTED.get(scenario["scenario_id"], {}).items():
        if quantity is None:
            expected_final.pop(product)
        else:
            expected_final[product] = quantity
    responses = []
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client,
    ):
        evidence["before"] = (await client.get("/api/quotes/" + quote_id)).json()
        response = await client.post(
            "/api/chat/sessions",
            json={key: scenario[key] for key in ("customer_id", "quote_id", "channel")},
        )
        assert response.status_code == 201, response.text
        session_id = response.json()["session_id"]
        payload = {
            "session_id": session_id,
            "message_id": uuid4().hex,
            "quote_id": quote_id,
            "message": scenario["user_message"],
            "channel": scenario["channel"],
        }
        for _ in range(2 if scenario.get("repeat_same_message_id") else 1):
            response = await client.post("/api/chat", json=payload)
            assert response.status_code == 200, response.text
            responses.append(response.json())
            evidence["responses"] = responses
        final = (await client.get("/api/quotes/" + quote_id)).json()
        evidence["after"] = final
    async with db.connect() as conn:
        logs = (
            (
                await conn.execute(
                    sa.select(tool_call_logs)
                    .where(tool_call_logs.c.session_id == session_id)
                    .order_by(tool_call_logs.c.log_id)
                )
            )
            .mappings()
            .all()
        )
        all_rows = (
            (await conn.execute(sa.select(quote_items).order_by(quote_items.c.quote_item_id)))
            .mappings()
            .all()
        )
        final_stock = (
            await conn.execute(
                sa.select(products.c.product_id, products.c.stock_qty).order_by(
                    products.c.product_id
                )
            )
        ).all()
    evidence["actual_tools"] = [dict(r) for r in logs]
    evidence["after_rows"] = [dict(r) for r in all_rows]
    evidence["after_stock"] = [dict(r._mapping) for r in final_stock]
    evidence["source_ids"] = sorted({s["source_id"] for r in responses for s in r["sources"]})
    assert final_stock == original_stock
    assert {
        r["product_id"]: r["quantity"]
        for r in all_rows
        if r["quote_id"] == quote_id and r["status"] == "active"
    } == expected_final
    assert [r for r in all_rows if r["quote_id"] != quote_id] == [
        r for r in original_rows if r["quote_id"] != quote_id
    ]
    if scenario["scenario_id"] not in EXPECTED:
        assert all_rows == original_rows
    for product, quantity in EXPECTED.get(scenario["scenario_id"], {}).items():
        if quantity is None:
            old = [r for r in all_rows if r["quote_id"] == quote_id and r["product_id"] == product]
            assert len(old) == 1 and old[0]["status"] == "replaced" and old[0]["replaced_by"]
    position = 0
    for expected in scenario["expected_tool_calls"]:
        while position < len(logs) and not matches(expected, logs[position], logs):
            position += 1
        assert position < len(logs), (expected, [(r["tool_name"], r["input"]) for r in logs])
        position += 1
    assert not set(scenario.get("must_not_call", [])) & {r["tool_name"] for r in logs}
    # Minimum ordered reads are allowed, but never tolerate extra writes.
    expected_mutations = [
        e["name"] for e in scenario["expected_tool_calls"] if e["name"] in MUTATIONS
    ]
    assert [r["tool_name"] for r in logs if r["tool_name"] in MUTATIONS] == expected_mutations
    for response in responses:
        source_ids = {s["source_id"] for s in response["sources"]}
        assert set(scenario["expected_sources"]) <= source_ids
        actual_sources = {
            s["source_id"]
            for r in logs
            if r["attempt_id"] == response["attempt_id"]
            for s in r["sources"]
        }
        assert source_ids <= actual_sources
        assert not set(scenario.get("must_not_recommend", [])) & set(
            response["recommended_product_ids"]
        )
        assert response["mode"] == "fallback" and response["provider_calls"] == 0
        assert response["text"]
    if scenario["scenario_id"] in NET:
        assert final["net_total_try"] == NET[scenario["scenario_id"]]
    if scenario["scenario_id"] == "SCN-006":
        assert "2d" in responses[-1]["text"].lower() and "1d" in responses[-1]["text"].lower()
    if scenario["scenario_id"] == "SCN-018":
        assert "kesin" in responses[-1]["text"].lower() and "vaat" in responses[-1]["text"].lower()
