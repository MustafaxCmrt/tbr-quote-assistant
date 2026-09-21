import asyncio
import json
import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.main import create_app
from app.persistence.database import make_engine
from app.persistence.models import (
    SEED_TABLES,
    bootstrap_state,
    products,
    quote_items,
)
from app.persistence.readiness import is_ready
from app.persistence.seed import SOURCE_DIR, load_seed, seed_database
from tests.conftest import migrate

EXPECTED = dict(zip((table.name for table in SEED_TABLES), (48, 22, 6, 10, 8, 6)))


async def snapshot(engine):
    async with engine.connect() as connection:
        return {
            table.name: [
                dict(row)
                for row in (
                    await connection.execute(sa.select(table).order_by(*table.primary_key.columns))
                ).mappings()
            ]
            for table in SEED_TABLES
        }


async def test_seed_preserves_all_original_fields_and_counts(db):
    assert await seed_database(db) == EXPECTED
    original = {
        table.name: json.loads((SOURCE_DIR / f"{table.name}.json").read_text(), parse_float=Decimal)
        for table in SEED_TABLES
    }
    actual = await snapshot(db)
    for table in SEED_TABLES:
        key = next(iter(table.primary_key.columns)).name
        by_id = {row[key]: row for row in actual[table.name]}
        assert len(by_id) == EXPECTED[table.name]
        for row in original[table.name]:
            observed = {field: by_id[row[key]][field] for field in row}
            if "effective_from" in observed:
                observed["effective_from"] = observed["effective_from"].isoformat()
            assert observed == row
    assert isinstance(actual["products"][0]["price_try"], Decimal)
    stock = {row["product_id"]: row["stock_qty"] for row in actual["products"]}
    out_of_stock = [row for row in actual["quote_items"] if stock[row["product_id"]] == 0]
    assert out_of_stock, "Fixture must exercise the original zero-stock draft items"
    assert all(row["fulfillment_status"] == "out_of_stock" for row in out_of_stock)


async def test_repeated_seed_preserves_edits_and_concurrent_calls(db):
    await seed_database(db)
    original, _ = load_seed()
    product_id = original["products"][0]["product_id"]
    async with db.begin() as connection:
        await connection.execute(
            products.update()
            .where(products.c.product_id == product_id)
            .values(name_tr="Kullanıcı düzenlemesi", price_try=Decimal("123.45"))
        )
    before = await snapshot(db)
    results = await asyncio.gather(seed_database(db), seed_database(db))
    assert results == [{name: 0 for name in EXPECTED}] * 2
    assert await snapshot(db) == before


async def test_seed_failure_rolls_back_every_table_and_marker(db, tmp_path):
    for table in SEED_TABLES:
        rows = json.loads((SOURCE_DIR / f"{table.name}.json").read_text())
        if table.name == "price_rules":
            rows[0]["discount_percent"] = 101
        (tmp_path / f"{table.name}.json").write_text(json.dumps(rows))
    with pytest.raises(IntegrityError):
        await seed_database(db, tmp_path)
    assert all(rows == [] for rows in (await snapshot(db)).values())
    async with db.connect() as connection:
        assert await connection.scalar(sa.select(sa.func.count()).select_from(bootstrap_state)) == 0
    assert not await is_ready(db)


async def test_unique_active_item_and_history_and_checks(db):
    await seed_database(db)
    rows, _ = load_seed()
    item = dict(rows["quote_items"][0], quote_item_id="TEST-DUP")
    with pytest.raises(IntegrityError):
        async with db.begin() as connection:
            await connection.execute(quote_items.insert().values(item))
    # Historical rows do not consume the one-active-product slot.
    async with db.begin() as connection:
        await connection.execute(
            quote_items.insert().values(dict(item, status="removed", quantity=0))
        )
    for changed in (
        {"quantity": -1},
        {"quantity": 0},
        {"unit_price_try": -1},
        {"product_id": "MISSING"},
        {"quote_id": "MISSING"},
    ):
        with pytest.raises(IntegrityError):
            async with db.begin() as connection:
                await connection.execute(
                    quote_items.update()
                    .where(quote_items.c.quote_item_id == rows["quote_items"][0]["quote_item_id"])
                    .values(**changed)
                )
    async with db.connect() as connection:
        assert await connection.scalar(sa.select(sa.func.count()).select_from(quote_items)) == 9


async def test_ready_requires_migration_and_seed_and_safe_http(empty_db):
    app = create_app(empty_db)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        assert (await client.get("/health/live")).json() == {"status": "ok"}
        response = await client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {
            "status": "not_ready",
            "detail": "Veritabanı henüz hazır değil.",
        }
        await migrate(empty_db)
        assert (await client.get("/health/ready")).status_code == 503
        await seed_database(empty_db)
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        async with empty_db.begin() as connection:
            await connection.execute(sa.text("UPDATE alembic_version SET version_num = 'stale'"))
        assert (await client.get("/health/ready")).status_code == 503


async def test_unavailable_database_is_not_ready():
    engine = make_engine("postgresql+asyncpg://nobody:invalid@127.0.0.1:1/missing")
    try:
        assert not await is_ready(engine)
        assert not await is_ready(None)
    finally:
        await engine.dispose()


async def test_runtime_role_can_read_but_cannot_change_schema_or_marker(db):
    await seed_database(db)
    engine = make_engine(db.url.set(username="tbr_runtime", password=os.environ["APP_DB_PASSWORD"]))
    try:
        assert await is_ready(engine)
        async with engine.begin() as connection:
            assert await connection.scalar(sa.select(sa.func.count()).select_from(products)) == 48
            await connection.execute(products.update().values(notes="runtime write permitted"))
        for statement in (
            "CREATE TABLE forbidden (id int)",
            "DELETE FROM bootstrap_state",
            "ALTER TABLE products ADD COLUMN forbidden int",
        ):
            with pytest.raises(DBAPIError):
                async with engine.begin() as connection:
                    await connection.execute(sa.text(statement))
    finally:
        await engine.dispose()
