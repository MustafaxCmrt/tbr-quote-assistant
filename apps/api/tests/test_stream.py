import json

import httpx
import pytest
import sqlalchemy as sa

from app.main import create_app
from app.persistence.models import mutation_receipts, tool_call_logs
from app.persistence.seed import seed_database
from app.services.executor import execute_plan
from tests.test_chat import message, open_session
from tests.test_mutations import prepare


def frames(response):
    assert response.headers["content-type"].startswith("text/event-stream")
    parsed = []
    for block in response.text.strip().split("\n\n"):
        wire, data = block.split("\n", 1)
        payload = json.loads(data.removeprefix("data: "))
        assert wire == "event: " + payload["type"]
        parsed.append(payload)
    assert [p["event_seq"] for p in parsed] == list(range(1, len(parsed) + 1))
    assert {p["schema_version"] for p in parsed} == {1}
    assert len({p["attempt_id"] for p in parsed}) == 1
    return parsed


@pytest.mark.parametrize(
    "quote,customer,text,product,total",
    [
        ("Q-1001", "CUST-IST-001", "Kablosuz barkod okuyucudan 1 tane daha ekle.", "PRD-BC-110", 2),
        (
            "Q-2001",
            "CUST-EXT-001",
            "BlueScan Air Plus modelinden 1 tane daha ekle.",
            "PRD-BC-110-PLUS",
            2,
        ),
    ],
)
async def test_stream_retry_actual_wrapper_and_log_correlation(
    db, quote, customer, text, product, total
):
    await seed_database(db)
    app = create_app(db)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client,
    ):
        session = await open_session(client, quote, customer)
        data = message(session, text, quote)
        attempts = []
        for _ in range(2):
            response = await client.post("/api/chat/stream", json=data)
            assert response.status_code == 200, response.text
            events = frames(response)
            attempts.append(events)
            assert events[0]["type"] == "message_start" and events[-1]["type"] == "done"
            assert "error" not in [e["type"] for e in events]
            assert "".join(e["payload"]["text"] for e in events if e["type"] == "text_delta")
            for event in events:
                assert event["session_id"] == session and event["message_id"] == data["message_id"]
            async with db.connect() as conn:
                logs = (
                    (
                        await conn.execute(
                            sa.select(tool_call_logs)
                            .where(tool_call_logs.c.attempt_id == events[0]["attempt_id"])
                            .order_by(tool_call_logs.c.tool_sequence)
                        )
                    )
                    .mappings()
                    .all()
                )
            results = [e["payload"] for e in events if e["type"] == "tool_call_result"]
            assert len(results) == len(logs)
            assert [
                (r["name"], r["tool_sequence"], r["output"], r["replayed"], r["mutation_applied"])
                for r in results
            ] == [
                (
                    r["tool_name"],
                    r["tool_sequence"],
                    r["output"],
                    r["replayed"],
                    r["mutation_applied"],
                )
                for r in logs
            ]
        first = next(
            e["payload"]
            for e in attempts[0]
            if e["type"] == "tool_call_result" and e["payload"]["name"] == "add_to_quote"
        )
        replay = next(
            e["payload"]
            for e in attempts[1]
            if e["type"] == "tool_call_result" and e["payload"]["name"] == "add_to_quote"
        )
        assert first["mutation_applied"] and not first["replayed"]
        assert replay["replayed"] and not replay["mutation_applied"]
        assert first["output"]["idempotency_key"] == replay["output"]["idempotency_key"]
        current = (await client.get("/api/quotes/" + quote)).json()
        assert next(p for p in current["items"] if p["product_id"] == product)["quantity"] == total
        history = (await client.get(f"/api/chat/sessions/{session}/messages")).json()
        assert len(history) == 1 and history[0]["status"] == "completed"
        assert history[0]["final_response"]["quote"]["version"] == current["version"]


async def test_stream_guard_error_no_success_or_partial_commit(db):
    await seed_database(db)
    app = create_app(db)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client,
    ):
        session = await open_session(client)
        before = (await client.get("/api/quotes/Q-1001")).json()
        data = message(session, "BlueScan Air 900 adet ekle.")
        response = await client.post("/api/chat/stream", json=data)
        events = frames(response)
        assert events[-1]["type"] == "error"
        assert events[-1]["payload"]["code"] == "INSUFFICIENT_STOCK"
        assert events[-1]["payload"]["committed"] is False
        assert not {"done", "tool_call_result"} & {e["type"] for e in events}
        assert (await client.get("/api/quotes/Q-1001")).json() == before
        logs = (await client.get("/api/tool-calls", params={"session_id": session})).json()
        assert len(logs) == 1 and logs[0]["success"] is False
        assert logs[0]["tool_name"] == "add_to_quote" and logs[0]["mutation_applied"] is False


async def test_executor_emits_no_success_from_rolled_back_group(db):
    await seed_database(db)
    session, msg = await prepare(
        db,
        [
            {"name": "add_to_quote", "arguments": {"product_id": "PRD-BC-110", "quantity": 1}},
            {"name": "add_to_quote", "arguments": {"product_id": "PRD-BC-120", "quantity": 900}},
        ],
    )
    events = []
    from app.services.errors import DomainError

    with pytest.raises(DomainError):
        await execute_plan(
            db, session, msg, on_event=lambda name, payload: events.append((name, payload))
        )
    assert [e[0] for e in events] == ["tool_call_start", "tool_call_start"]
    async with db.connect() as conn:
        assert await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts)) == 0


async def test_disconnect_after_commit_and_reconnect_keeps_single_effect(db):
    import asyncio

    from app.orchestration.chat import create_session, process_chat
    from app.orchestration.streaming import ACTIVE_STREAMS, stream_chat
    from app.schemas.chat import ChatInput, SessionInput

    await seed_database(db)
    session = await create_session(db, SessionInput(customer_id="CUST-IST-001", quote_id="Q-1001"))
    request = ChatInput(**message(session["session_id"], "Kablosuz okuyucudan 1 tane daha ekle."))
    stream = stream_chat(db, request)
    while True:
        frame = await anext(stream)
        if "event: tool_call_result" in frame:
            break
    await stream.aclose()  # Consumer abort only, accepted task completes independently.
    await asyncio.wait_for(asyncio.gather(*list(ACTIVE_STREAMS)), 5)
    replay = await process_chat(db, request)
    assert replay["quote"]["items"][0]["quantity"] == 2
    async with db.connect() as conn:
        rows = (
            (
                await conn.execute(
                    sa.select(tool_call_logs)
                    .where(
                        tool_call_logs.c.message_id == request.message_id,
                        tool_call_logs.c.tool_name == "add_to_quote",
                    )
                    .order_by(tool_call_logs.c.log_id)
                )
            )
            .mappings()
            .all()
        )
        assert [(r["replayed"], r["mutation_applied"]) for r in rows] == [
            (False, True),
            (True, False),
        ]
        assert await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts)) == 1


async def test_error_after_commit_reports_truth_and_masks_exception(db, monkeypatch):
    from app.orchestration import chat

    await seed_database(db)
    app = create_app(db)
    original = chat.render

    def broken(*args):
        raise RuntimeError("PRIVATE_DIAGNOSTIC_DO_NOT_EXPOSE")

    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client,
    ):
        session = await open_session(client)
        data = message(session, "Kablosuz okuyucudan 1 tane daha ekle.")
        monkeypatch.setattr(chat, "render", broken)
        response = await client.post("/api/chat/stream", json=data)
        events = frames(response)
        assert events[-1]["type"] == "error" and events[-1]["payload"]["committed"] is True
        assert events[-1]["payload"]["code"] == "INTERNAL_ERROR"
        assert "PRIVATE_DIAGNOSTIC_DO_NOT_EXPOSE" not in response.text
        assert "done" not in [e["type"] for e in events]
        monkeypatch.setattr(chat, "render", original)
        recovered = await client.post("/api/chat/stream", json=data)
        result = frames(recovered)
        assert result[-1]["type"] == "done"
        mutation = next(
            e["payload"]
            for e in result
            if e["type"] == "tool_call_result" and e["payload"]["name"] == "add_to_quote"
        )
        assert mutation["replayed"] and not mutation["mutation_applied"]
        assert (await client.get("/api/quotes/Q-1001")).json()["items"][0]["quantity"] == 2
