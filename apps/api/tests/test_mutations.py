import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa

from app.persistence.models import (
    chat_messages,
    chat_sessions,
    mutation_receipts,
    products,
    tool_call_logs,
)
from app.persistence.seed import seed_database
from app.services.errors import DomainError
from app.services.execution_context import action_key
from app.services.executor import execute_plan
from app.services.quotes import get_quote


async def prepare(
    db,
    plan,
    *,
    quote_id="Q-1001",
    customer_id="CUST-IST-001",
    constraints=None,
    message_id=None,
    session_id=None,
):
    session_id = session_id or uuid4().hex
    message_id = message_id or uuid4().hex
    for index, step in enumerate(plan):
        step["arguments"].setdefault("quote_id", quote_id)
        if step["name"] in {"add_to_quote", "replace_with_alternative"}:
            step["arguments"].setdefault(
                "idempotency_key", action_key(quote_id, message_id, index, step["name"])
            )
        if step["name"] == "add_to_quote":
            step["arguments"].setdefault("source_message_id", message_id)
    async with db.begin() as conn:
        await conn.execute(
            chat_sessions.insert().values(
                session_id=session_id,
                customer_id=customer_id,
                quote_id=quote_id,
                channel="mobile",
                locale="tr",
            )
        )
        await conn.execute(
            chat_messages.insert().values(
                session_id=session_id,
                message_id=message_id,
                body="genel test komutu",
                payload_hash="test",
                trusted_constraints=constraints or {},
                persisted_plan=plan,
            )
        )
    return session_id, message_id


def add(product="PRD-BC-110", quantity=1):
    return {"name": "add_to_quote", "arguments": {"product_id": product, "quantity": quantity}}


def update(quantity):
    return {
        "name": "update_quote_item",
        "arguments": {
            "product_id": "PRD-BC-110",
            "quantity": quantity,
            "reason": "Kullanıcı miktarı değiştirdi",
        },
    }


def replace(source="PRD-BC-130", target="PRD-BC-140", quantity=None):
    return {
        "name": "replace_with_alternative",
        "arguments": {
            "from_product_id": source,
            "to_product_id": target,
            "quantity": quantity,
            "reason": "Stoklu alternatif",
        },
    }


async def current(db, quote_id="Q-1001"):
    async with db.connect() as conn:
        return await get_quote(conn, quote_id)


async def test_add_retry_new_message_and_real_wrapper_logs(db):
    await seed_database(db)
    ids = await prepare(db, [add(quantity=2)])
    first = await execute_plan(db, *ids)
    second = await execute_plan(db, *ids)
    assert first[0]["mutation_applied"] is True
    assert second[0]["replayed"] is True and second[0]["mutation_applied"] is False
    assert (await current(db)).items[0].quantity == 3
    assert (await current(db)).version == 2
    more = await prepare(db, [add(quantity=2)])
    await execute_plan(db, *more)
    assert (await current(db)).items[0].quantity == 5
    async with db.connect() as conn:
        logs = (
            (
                await conn.execute(
                    sa.select(tool_call_logs)
                    .where(tool_call_logs.c.message_id == ids[1])
                    .order_by(tool_call_logs.c.log_id)
                )
            )
            .mappings()
            .all()
        )
        assert [(r["tool_name"], r["replayed"], r["mutation_applied"]) for r in logs] == [
            ("add_to_quote", False, True),
            ("add_to_quote", True, False),
        ]
        assert (
            await conn.scalar(
                sa.select(products.c.stock_qty).where(products.c.product_id == "PRD-BC-110")
            )
            == 18
        )


async def test_same_and_distinct_key_concurrency(db):
    await seed_database(db)
    ids = await prepare(db, [add()])
    result = await asyncio.gather(execute_plan(db, *ids), execute_plan(db, *ids))
    assert sorted(r[0]["replayed"] for r in result) == [False, True]
    others = [await prepare(db, [add()]) for _ in range(2)]
    await asyncio.gather(*(execute_plan(db, *ident) for ident in others))
    quote = await current(db)
    assert len(quote.items) == 1 and quote.items[0].quantity == 4 and quote.version == 4


async def test_changed_payload_conflict_and_stale_update_replay(db):
    await seed_database(db)
    ids = await prepare(db, [update(4)])
    await execute_plan(db, *ids)
    newer = await prepare(db, [update(2)])
    await execute_plan(db, *newer)
    assert (await execute_plan(db, *ids))[0]["replayed"] is True
    assert (await current(db)).items[0].quantity == 2
    async with db.begin() as conn:
        plan = [update(5)]
        plan[0]["arguments"]["quote_id"] = "Q-1001"
        await conn.execute(
            chat_messages.update()
            .where(chat_messages.c.message_id == ids[1])
            .values(persisted_plan=plan)
        )
    with pytest.raises(DomainError, match="IDEMPOTENCY_CONFLICT"):
        await execute_plan(db, *ids)
    assert (await current(db)).items[0].quantity == 2


async def test_group_rollback_and_two_distinct_action_keys(db):
    await seed_database(db)
    bad = await prepare(db, [add(), add("MISSING")])
    with pytest.raises(DomainError, match="PRODUCT_NOT_FOUND"):
        await execute_plan(db, *bad)
    assert (await current(db)).items[0].quantity == 1
    async with db.connect() as conn:
        assert await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts)) == 0
        assert (
            await conn.scalar(
                sa.select(sa.func.count())
                .select_from(tool_call_logs)
                .where(tool_call_logs.c.success.is_(True))
            )
            == 0
        )
    good = await prepare(db, [add(), add()])
    results = await execute_plan(db, *good)
    assert len(results) == 2 and all(r["mutation_applied"] for r in results)
    assert (await current(db)).items[0].quantity == 3
    async with db.connect() as conn:
        keys = (await conn.execute(sa.select(mutation_receipts.c.idempotency_key))).scalars().all()
        assert len(keys) == len(set(keys)) == 2


@pytest.mark.parametrize(
    ("product", "quantity", "constraints", "code"),
    [
        ("PRD-BC-110", 1, {"max_price_try": "7989.99"}, "PRICE_LIMIT_EXCEEDED"),
        ("PRD-BC-140", 1, {"required_tags": ["qr"]}, "REQUIRED_FEATURE_MISSING"),
        ("PRD-BC-130", 1, {}, "OUT_OF_STOCK"),
        ("PRD-BC-130", 1, {"explicit_backorder_consent": True}, "OUT_OF_STOCK"),
        ("PRD-BC-110", 18, {}, "INSUFFICIENT_STOCK"),
    ],
)
async def test_mutation_guards_cannot_be_bypassed(db, product, quantity, constraints, code):
    await seed_database(db)
    ids = await prepare(db, [add(product, quantity)], constraints=constraints)
    before = await current(db)
    with pytest.raises(DomainError, match=code):
        await execute_plan(db, *ids)
    assert await current(db) == before


async def test_replace_history_merge_and_removal_ignores_source_guards(db):
    await seed_database(db)
    ids = await prepare(db, [replace()], quote_id="Q-1005")
    await execute_plan(db, *ids)
    quote = await current(db, "Q-1005")
    assert [(i.product_id, i.quantity) for i in quote.items] == [("PRD-BC-140", 2)]
    assert quote.history[0].status == "replaced"
    assert quote.history[0].replaced_by == quote.items[0].quote_item_id
    async with db.begin() as conn:
        await conn.execute(
            products.update()
            .where(products.c.product_id == "PRD-BC-110")
            .values(active=False, stock_qty=0)
        )
    remove = await prepare(db, [update(0)], constraints={"max_price_try": "1"})
    await execute_plan(db, *remove)
    quote = await current(db)
    assert (
        quote.items == []
        and quote.history[0].status == "removed"
        and quote.net_total_try == Decimal(0)
    )


@pytest.mark.parametrize("consent", [False, True])
async def test_backorder_requires_eligible_customer_and_explicit_consent(db, consent):
    await seed_database(db)
    ids = await prepare(
        db,
        [add("PRD-BC-130")],
        quote_id="Q-1002",
        customer_id="CUST-ANK-002",
        constraints={"explicit_backorder_consent": consent},
    )
    if consent:
        await execute_plan(db, *ids)
        quote = await current(db, "Q-1002")
        assert quote.items[0].fulfillment_status == "backorder"
        assert quote.items[0].quantity == 1
    else:
        with pytest.raises(DomainError, match="OUT_OF_STOCK"):
            await execute_plan(db, *ids)
        assert (await current(db, "Q-1002")).items == []


async def test_replace_merges_and_rejects_backorder_even_with_consent(db):
    await seed_database(db)
    ids = await prepare(db, [add("PRD-BC-140"), replace()], quote_id="Q-1005")
    await execute_plan(db, *ids)
    quote = await current(db, "Q-1005")
    assert [(i.product_id, i.quantity) for i in quote.items] == [("PRD-BC-140", 3)]
    assert len(quote.history) == 1
    # Existing BC-110 permits BC-130 as a substitute only if source dataset says so.
    async with db.begin() as conn:
        await conn.execute(
            products.update()
            .where(products.c.product_id == "PRD-BC-110-PLUS")
            .values(substitute_product_ids=["PRD-BC-130"])
        )
    backorder = await prepare(
        db,
        [replace("PRD-BC-110-PLUS", "PRD-BC-130")],
        quote_id="Q-2001",
        customer_id="CUST-EXT-001",
        constraints={"explicit_backorder_consent": True},
    )
    before = await current(db, "Q-2001")
    with pytest.raises(DomainError, match="OUT_OF_STOCK"):
        await execute_plan(db, *backorder)
    assert await current(db, "Q-2001") == before


@pytest.mark.parametrize(
    ("changed", "code"),
    [({"price_try": Decimal(9000)}, "PRICE_LIMIT_EXCEEDED"), ({"stock_qty": 0}, "OUT_OF_STOCK")],
)
async def test_admin_update_lock_cannot_race_price_or_stock_guard(db, changed, code):
    await seed_database(db)
    ids = await prepare(db, [add()], constraints={"max_price_try": "8500"})
    task = None
    async with db.connect() as admin:
        transaction = await admin.begin()
        try:
            admin_pid = await admin.scalar(sa.text("SELECT pg_backend_pid()"))
            await admin.execute(
                products.update().where(products.c.product_id == "PRD-BC-110").values(**changed)
            )
            task = asyncio.create_task(execute_plan(db, *ids))
            blocked = 0
            for _ in range(100):
                async with db.connect() as observer:
                    blocked = await observer.scalar(
                        sa.text(
                            "SELECT count(*) FROM pg_stat_activity WHERE :pid = ANY(pg_blocking_pids(pid))"
                        ),
                        {"pid": admin_pid},
                    )
                if blocked:
                    break
                await asyncio.sleep(0.01)
            assert blocked > 0, (
                "Executor must wait for product row lock, not read stale price/stock"
            )
            await transaction.commit()
            with pytest.raises(DomainError, match=code):
                await asyncio.wait_for(task, 3)
            assert (await current(db)).items[0].quantity == 1
        finally:
            if transaction.is_active:
                await transaction.rollback()
            if task and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        ({"quote_id": "Q-1002"}, "QUOTE_CONTEXT_MISMATCH"),
        ({"idempotency_key": "client-supplied"}, "IDEMPOTENCY_CONFLICT"),
        ({"source_message_id": "other-message"}, "QUOTE_CONTEXT_MISMATCH"),
        ({"quantity": -1}, "INVALID_INPUT"),
        ({"quantity": 0}, "INVALID_INPUT"),
        ({"quantity": True}, "INVALID_INPUT"),
    ],
)
async def test_forged_input_and_invalid_quantity_leave_quote_unchanged(db, arguments, code):
    await seed_database(db)
    step = add()
    step["arguments"].update(arguments)
    ids = await prepare(db, [step])
    before = await current(db)
    with pytest.raises(DomainError, match=code):
        await execute_plan(db, *ids)
    assert await current(db) == before


async def test_plus_guard_and_reconnect_retry_keep_snapshot(db):
    await seed_database(db)
    unapproved = await prepare(
        db, [add("PRD-BC-110-PLUS")], quote_id="Q-2001", customer_id="CUST-EXT-001"
    )
    with pytest.raises(DomainError, match="EXPLICIT_VARIANT_REQUIRED"):
        await execute_plan(db, *unapproved)
    ids = await prepare(
        db,
        [add("PRD-BC-110-PLUS", 3)],
        quote_id="Q-2001",
        customer_id="CUST-EXT-001",
        constraints={"explicit_plus": True},
    )
    await execute_plan(db, *ids)
    await db.dispose()  # Simulate loss of process-local pooled connection state.
    result = await execute_plan(db, *ids)
    assert result[0]["replayed"] is True
    quote = await current(db, "Q-2001")
    assert quote.items[0].quantity == 4
    assert quote.net_total_try == Decimal("35456.80")


@pytest.mark.parametrize(
    ("change", "constraints", "code"),
    [
        ({"active": False}, {}, "PRODUCT_INACTIVE"),
        ({"min_order_qty": 4}, {}, "MIN_ORDER_NOT_MET"),
        ({"price_try": Decimal(1)}, {"max_price_try": "5000"}, "PRICE_LIMIT_EXCEEDED"),
    ],
)
async def test_active_minimum_and_existing_snapshot_guard(db, change, constraints, code):
    await seed_database(db)
    async with db.begin() as conn:
        await conn.execute(
            products.update().where(products.c.product_id == "PRD-BC-110").values(**change)
        )
    ids = await prepare(db, [add()], constraints=constraints)
    before = await current(db)
    with pytest.raises(DomainError, match=code):
        await execute_plan(db, *ids)
    assert await current(db) == before


@pytest.mark.parametrize(
    ("step", "constraints", "code"),
    [
        (replace("PRD-BC-130", "PRD-BC-130"), {}, "INVALID_ALTERNATIVE"),
        (replace("PRD-BC-130", "PRD-SW-520"), {}, "INVALID_ALTERNATIVE"),
        (replace(), {"required_tags": ["qr"]}, "REQUIRED_FEATURE_MISSING"),
        (replace(), {"max_price_try": "5349.99"}, "PRICE_LIMIT_EXCEEDED"),
    ],
)
async def test_replace_alternative_constraints(db, step, constraints, code):
    await seed_database(db)
    ids = await prepare(db, [step], quote_id="Q-1005", constraints=constraints)
    before = await current(db, "Q-1005")
    with pytest.raises(DomainError, match=code):
        await execute_plan(db, *ids)
    assert await current(db, "Q-1005") == before


async def test_runtime_db_role_executes_atomic_mutation(db):
    import os

    from app.persistence.database import make_engine

    await seed_database(db)
    ids = await prepare(db, [add()])
    runtime = make_engine(
        db.url.set(username="tbr_runtime", password=os.environ["APP_DB_PASSWORD"])
    )
    try:
        assert (await execute_plan(runtime, *ids))[0]["mutation_applied"] is True
        assert (await current(runtime)).items[0].quantity == 2
    finally:
        await runtime.dispose()


@pytest.mark.parametrize(
    ("quote_id", "customer", "plan", "expected", "net"),
    [
        (
            "Q-1003",
            "CUST-IST-001",
            [
                {
                    "name": "update_quote_item",
                    "arguments": {"product_id": "PRD-PRN-320", "quantity": 4, "reason": "Miktar"},
                }
            ],
            [("PRD-PRN-320", 4)],
            "29400.00",
        ),
        (
            "Q-1004",
            "CUST-IST-001",
            [replace("PRD-BC-120", "PRD-BC-110")],
            [("PRD-BC-110", 1)],
            "7990.00",
        ),
        (
            "Q-2004",
            "CUST-EXT-001",
            [replace("PRD-PRN-330", "PRD-PRN-320")],
            [("PRD-PRN-320", 1)],
            "7350.00",
        ),
        (
            "Q-2005",
            "CUST-EXT-002",
            [
                {
                    "name": "update_quote_item",
                    "arguments": {
                        "product_id": "PRD-SVC-810",
                        "quantity": 2,
                        "reason": "İki lokasyon",
                    },
                }
            ],
            [("PRD-SVC-810", 2)],
            "9000.00",
        ),
        ("Q-1002", "CUST-ANK-002", [add(quantity=3)], [("PRD-BC-110", 3)], "22292.10"),
        (
            "Q-1002",
            "CUST-ANK-002",
            [add("PRD-SW-520"), add("PRD-SW-530")],
            [("PRD-SW-520", 1), ("PRD-SW-530", 1)],
            "22816.00",
        ),
    ],
)
async def test_domain_examples_with_exact_net_totals(db, quote_id, customer, plan, expected, net):
    await seed_database(db)
    ids = await prepare(db, plan, quote_id=quote_id, customer_id=customer)
    await execute_plan(db, *ids)
    result = await current(db, quote_id)
    assert sorted((i.product_id, i.quantity) for i in result.items) == expected
    assert result.net_total_try == Decimal(net)


@pytest.mark.parametrize(
    ("change", "constraints", "code"),
    [
        ({}, {"max_price_try": "7989.99"}, "PRICE_LIMIT_EXCEEDED"),
        ({"stock_qty": 0}, {}, "OUT_OF_STOCK"),
        ({"active": False}, {}, "PRODUCT_INACTIVE"),
        ({}, {"required_tags": ["1d"]}, "REQUIRED_FEATURE_MISSING"),
    ],
)
async def test_positive_update_rechecks_guards(db, change, constraints, code):
    await seed_database(db)
    if change:
        async with db.begin() as conn:
            await conn.execute(
                products.update().where(products.c.product_id == "PRD-BC-110").values(**change)
            )
    ids = await prepare(db, [update(4)], constraints=constraints)
    before = await current(db)
    with pytest.raises(DomainError, match=code):
        await execute_plan(db, *ids)
    assert await current(db) == before


async def test_mutation_accepts_exact_price_and_stock_boundaries(db):
    await seed_database(db)
    ids = await prepare(db, [add(quantity=17)], constraints={"max_price_try": "7990.00"})
    await execute_plan(db, *ids)
    quote = await current(db)
    assert quote.items[0].quantity == 18
    assert quote.items[0].unit_price_try == Decimal("7990.00")
    assert quote.net_total_try == Decimal("143820.00")


async def test_add_preserves_existing_snapshot_after_catalog_price_change(db):
    await seed_database(db)
    async with db.begin() as conn:
        await conn.execute(
            products.update()
            .where(products.c.product_id == "PRD-BC-110")
            .values(price_try=Decimal("5000.00"))
        )
    ids = await prepare(db, [add()])
    await execute_plan(db, *ids)
    quote = await current(db)
    assert quote.items[0].quantity == 2
    assert quote.items[0].unit_price_try == Decimal("7990.00")
    assert quote.net_total_try == Decimal("15980.00")


async def test_positive_update_insufficient_stock_preserves_receipts_and_version(db):
    await seed_database(db)
    ids = await prepare(db, [update(19)])
    before = await current(db)
    with pytest.raises(DomainError, match="INSUFFICIENT_STOCK"):
        await execute_plan(db, *ids)
    assert await current(db) == before
    async with db.connect() as conn:
        assert await conn.scalar(sa.select(sa.func.count()).select_from(mutation_receipts)) == 0


@pytest.mark.parametrize("merge", [False, True])
async def test_explicit_replacement_quantity_overrides_source_quantity(db, merge):
    await seed_database(db)
    plan = ([add("PRD-BC-140")] if merge else []) + [replace(quantity=1)]
    ids = await prepare(db, plan, quote_id="Q-1005")
    await execute_plan(db, *ids)
    quote = await current(db, "Q-1005")
    assert [(i.product_id, i.quantity) for i in quote.items] == [("PRD-BC-140", 2 if merge else 1)]
    assert quote.history[0].quantity == 2 and quote.history[0].status == "replaced"
