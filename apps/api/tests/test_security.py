import json

import httpx
import sqlalchemy as sa

from app import main
from app.main import create_app
from app.orchestration import streaming
from app.persistence.models import knowledge_entries, products
from app.persistence.seed import seed_database
from app.schemas.chat import ChatInput

KEY = "test-admin-key"


def client_for(app, **kwargs):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test", **kwargs
    )


async def counts(db):
    async with db.connect() as conn:
        return (
            await conn.scalar(sa.select(sa.func.count()).select_from(products)),
            await conn.scalar(sa.select(sa.func.count()).select_from(knowledge_entries)),
        )


async def test_admin_writes_require_the_configured_key_and_reads_stay_open(db, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", KEY)
    await seed_database(db)
    app = create_app(db)
    product = {
        "sku": "TBR-AUTH-1",
        "name_tr": "Yetkisiz Ürün",
        "category": "accessory",
        "brand": "Deneme",
        "price_try": "10.00",
        "stock_qty": 1,
    }
    knowledge = {
        "topic": "fallback",
        "title": "Yetkisiz kayıt",
        "body": "Bu metin hiçbir yanıta girmemeli.",
        "source": "test",
        "effective_from": "2026-01-01",
    }
    before = await counts(db)
    writes = [
        ("POST", "/api/products", product),
        ("PATCH", "/api/products/PRD-BC-110", {"stock_qty": 0}),
        ("DELETE", "/api/products/PRD-BC-110", None),
        ("POST", "/api/knowledge", knowledge),
        ("PATCH", "/api/knowledge/KNE-FALL-001", {"body": "Değişti"}),
        ("DELETE", "/api/knowledge/KNE-FALL-001", None),
    ]
    async with app.router.lifespan_context(app), client_for(app) as client:
        for headers in ({}, {"X-Admin-Key": "wrong"}, {"X-Admin-Key": ""}):
            for method, path, body in writes:
                response = await client.request(method, path, json=body, headers=headers)
                assert response.status_code == 401, (method, path, response.text)
                assert response.json()["error"]["code"] == "ADMIN_KEY_REQUIRED"
        assert (await client.get("/api/products/PRD-BC-110")).json()["stock_qty"] > 0
        assert (await client.get("/api/knowledge/KNE-FALL-001")).json()["active"] is True
        assert (await client.get("/api/products", params={"limit": 1})).status_code == 200
        assert (await client.get("/api/knowledge", params={"limit": 1})).status_code == 200
        # Chat and quote flows used by web and mobile are not admin writes.
        session = await client.post(
            "/api/chat/sessions",
            json={"customer_id": "CUST-IST-001", "quote_id": "Q-1001", "channel": "mobile"},
        )
        assert session.status_code == 201, session.text
        assert (await client.get("/api/quotes/Q-1001")).status_code == 200
        created = await client.post("/api/products", json=product, headers={"X-Admin-Key": KEY})
        assert created.status_code == 201, created.text
    assert await counts(db) == (before[0] + 1, before[1])


async def test_admin_writes_fail_closed_without_server_key(db, monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    await seed_database(db)
    app = create_app(db)
    async with app.router.lifespan_context(app), client_for(app) as client:
        response = await client.patch(
            "/api/products/PRD-BC-110", json={"stock_qty": 0}, headers={"X-Admin-Key": ""}
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "ADMIN_KEY_NOT_CONFIGURED"
        assert (await client.get("/api/products/PRD-BC-110")).json()["stock_qty"] > 0


async def test_oversized_bodies_are_rejected_before_parsing(empty_db):
    app = create_app(empty_db)
    oversized = b'{"message":"' + b"x" * main.MAX_BODY_BYTES + b'"}'

    async def chunks():
        for start in range(0, len(oversized), 65536):
            yield oversized[start : start + 65536]

    async with app.router.lifespan_context(app), client_for(app) as client:
        declared = await client.post(
            "/api/chat", content=oversized, headers={"Content-Type": "application/json"}
        )
        assert declared.status_code == 413
        assert declared.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
        streamed = await client.post(
            "/api/chat", content=chunks(), headers={"Content-Type": "application/json"}
        )
        assert "content-length" not in streamed.request.headers
        assert streamed.status_code == 413
        assert streamed.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
        assert (await client.get("/health/live")).status_code == 200


class UnreachableEngine:
    def connect(self):
        raise TimeoutError


async def test_stream_emits_error_frame_when_commit_probe_cannot_reach_database(monkeypatch):
    async def database_lost(*args, **kwargs):
        raise OSError("connection lost")

    monkeypatch.setattr(streaming, "process_chat", database_lost)
    request = ChatInput(
        session_id="session", message_id="message", quote_id="Q-1001", message="İade süresi?"
    )
    frames = [frame async for frame in streaming.stream_chat(UnreachableEngine(), request)]
    assert [frame.split("\n", 1)[0] for frame in frames] == [
        "event: message_start",
        "event: error",
    ]
    error = json.loads(frames[-1].split("data: ", 1)[1])
    assert error["payload"]["code"] == "INTERNAL_ERROR"
    # Commit state is unknown, so the client must refetch instead of assuming nothing changed.
    assert error["payload"]["committed"] is True and error["payload"]["retryable"] is True
