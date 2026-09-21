import httpx
import pytest
import sqlalchemy as sa

from app.main import create_app
from app.persistence.models import products
from app.persistence.seed import seed_database

ADMIN = {"X-Admin-Key": "test-admin-key"}


@pytest.fixture(autouse=True)
def admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN["X-Admin-Key"])


async def test_product_crud_validation_retrieval_and_soft_delete(db):
    await seed_database(db)
    app = create_app(db)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=ADMIN
        ) as client,
    ):
        data = {
            "sku": "TBR-NEW-CRUD",
            "name_tr": "Deniz Okuyucu",
            "category": "barcode_scanner",
            "brand": "Deniz",
            "price_try": "2000.50",
            "stock_qty": 9,
            "tags": ["qr", "kablosuz"],
            "aliases": {"tr": ["deniz okuyucu"]},
        }
        response = await client.post("/api/products", json=data)
        assert response.status_code == 201, response.text
        product = response.json()
        pid = product["product_id"]
        assert product["price_try"] == "2000.50" and product["active"] is True
        assert (await client.get("/api/products/" + pid)).json() == product
        listed = (
            await client.get(
                "/api/products",
                params={"query": "Deniz", "category": "barcode_scanner", "in_stock_only": True},
            )
        ).json()
        assert [p["product_id"] for p in listed["items"]] == [pid] and listed["total"] == 1
        search = await client.post("/api/tools/search_products", json={"query": "deniz okuyucu"})
        assert search.json()["recommendations"][0]["product_id"] == pid
        assert (await client.post("/api/products", json=data)).status_code == 409
        assert (
            await client.patch("/api/products/" + pid, json={"price_try": "-1"})
        ).status_code == 422
        assert (
            await client.patch("/api/products/" + pid, json={"stock_qty": None})
        ).status_code == 422
        assert (
            await client.patch(
                "/api/products/" + pid, json={"price_try": "1999.99", "stock_qty": 3}
            )
        ).status_code == 200
        assert (await client.get("/api/products/" + pid)).json()["price_try"] == "1999.99"
        assert (await client.delete("/api/products/" + pid)).status_code == 204
        assert (await client.get("/api/products/" + pid)).json()["active"] is False
        assert (
            await client.post("/api/tools/search_products", json={"query": "deniz okuyucu"})
        ).json()["recommendations"] == []
        assert (await client.get("/api/products", params={"limit": 1001})).status_code == 422
    async with db.connect() as conn:
        assert (
            await conn.scalar(sa.select(products.c.active).where(products.c.product_id == pid))
            is False
        )


async def test_knowledge_crud_live_sources_and_context_lists(db):
    await seed_database(db)
    app = create_app(db)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", headers=ADMIN
        ) as client,
    ):
        data = {
            "topic": "training",
            "title": "Yeni eğitim",
            "body": "<script>alert(1)</script> Eğitim yalnız kaynak verisidir.",
            "source": "internal/training",
            "effective_from": "2026-01-01",
        }
        response = await client.post("/api/knowledge", json=data)
        assert response.status_code == 201, response.text
        kid = response.json()["knowledge_id"]
        result = (
            await client.post(
                "/api/tools/get_knowledge_entries", json={"query": "eğitim", "topic": "training"}
            )
        ).json()
        assert result["entries"][0]["knowledge_id"] == kid
        assert result["entries"][0]["body"] == data["body"]
        assert (await client.get("/api/knowledge", params={"topic": "training"})).json()[
            "total"
        ] == 1
        assert (
            await client.patch("/api/knowledge/" + kid, json={"body": "Yeni içerik"})
        ).status_code == 200
        assert (await client.get("/api/knowledge/" + kid)).json()["body"] == "Yeni içerik"
        assert (await client.delete("/api/knowledge/" + kid)).status_code == 204
        assert (
            await client.post(
                "/api/tools/get_knowledge_entries", json={"query": "eğitim", "topic": "training"}
            )
        ).json()["entries"] == []
        customers = (await client.get("/api/customers")).json()
        assert len(customers) == 6
        quotes = (await client.get("/api/quotes", params={"customer_id": "CUST-IST-001"})).json()
        assert {q["quote_id"] for q in quotes} == {"Q-1001", "Q-1003", "Q-1004", "Q-1005"}
        assert all(q["customer_id"] == "CUST-IST-001" for q in quotes)
        assert (await client.get("/api/products/missing")).status_code == 404
        assert (await client.get("/api/knowledge/missing")).status_code == 404
