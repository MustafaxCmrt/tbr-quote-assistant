"""Real wrappers; caller owns the transaction and quote/product locks."""

from uuid import uuid4

import sqlalchemy as sa

from app.persistence.models import mutation_receipts, quote_items, quotes
from app.schemas.tools import AddInput, ReplaceInput, UpdateInput
from app.services.errors import DomainError
from app.services.execution_context import action_key, payload_hash
from app.services.normalization import normalize
from app.services.quotes import get_quote


def fail(code, message):
    raise DomainError(code, message)


def product(context, product_id):
    row = context.catalog.get(product_id)
    if row is None:
        fail("PRODUCT_NOT_FOUND", "Ürün bulunamadı.")
    return row


def guard(context, row, quantity, *, snapshot=None, replace=False, selecting=True):
    if not row["active"]:
        fail("PRODUCT_INACTIVE", "Ürün satışa kapalı.")
    if selecting and row["sku"].endswith("PLUS") and not context.constraints.explicit_plus:
        fail("EXPLICIT_VARIANT_REQUIRED", "Plus varyantını açıkça seçmelisin.")
    ceiling = context.constraints.max_price_try
    if ceiling is not None and (
        row["price_try"] > ceiling or (snapshot is not None and snapshot > ceiling)
    ):
        fail("PRICE_LIMIT_EXCEEDED", "Ürün birim fiyatı belirtilen sınırı aşıyor.")
    required = set(map(normalize, context.constraints.required_tags))
    if not required <= set(map(normalize, row["tags"])):
        fail("REQUIRED_FEATURE_MISSING", "Ürün gerekli özellikleri karşılamıyor.")
    if quantity < row["min_order_qty"]:
        fail("MIN_ORDER_NOT_MET", "Asgari sipariş miktarı karşılanmıyor.")
    if row["stock_qty"] == 0:
        if replace or not (
            context.constraints.explicit_backorder_consent and context.customer["allow_backorder"]
        ):
            fail("OUT_OF_STOCK", "Ürün stokta yok; uygun müşteri ve açık bekleme onayı gerekir.")
        return "backorder"
    if quantity > row["stock_qty"]:
        fail("INSUFFICIENT_STOCK", "İstenen toplam miktar mevcut stoku aşıyor.")
    return "in_stock"


async def active_item(conn, quote_id, product_id):
    return (
        (
            await conn.execute(
                sa.select(quote_items).where(
                    quote_items.c.quote_id == quote_id,
                    quote_items.c.product_id == product_id,
                    quote_items.c.status == "active",
                )
            )
        )
        .mappings()
        .one_or_none()
    )


async def _add(conn, args, ctx):
    row = product(ctx, args.product_id)
    item = await active_item(conn, ctx.quote_id, args.product_id)
    quantity = args.quantity + (item["quantity"] if item else 0)
    fulfillment = guard(ctx, row, quantity, snapshot=item["unit_price_try"] if item else None)
    if item:
        await conn.execute(
            quote_items.update()
            .where(quote_items.c.quote_item_id == item["quote_item_id"])
            .values(quantity=quantity, fulfillment_status=fulfillment)
        )
        item_id = item["quote_item_id"]
    else:
        item_id = "QI-" + uuid4().hex
        await conn.execute(
            quote_items.insert().values(
                quote_item_id=item_id,
                quote_id=ctx.quote_id,
                product_id=args.product_id,
                quantity=quantity,
                unit_price_try=row["price_try"],
                status="active",
                source_message_id=ctx.message_id,
                idempotency_key=args.idempotency_key,
                fulfillment_status=fulfillment,
            )
        )
    return {"product_id": args.product_id, "quote_item_id": item_id, "quantity": quantity}


async def _update(conn, args, ctx):
    item = await active_item(conn, ctx.quote_id, args.product_id)
    if item is None:
        fail("QUOTE_ITEM_NOT_FOUND", "Aktif teklif kalemi bulunamadı.")
    if args.quantity == 0:
        await conn.execute(
            quote_items.update()
            .where(quote_items.c.quote_item_id == item["quote_item_id"])
            .values(quantity=0, status="removed")
        )
    else:
        fulfillment = guard(
            ctx,
            product(ctx, args.product_id),
            args.quantity,
            snapshot=item["unit_price_try"],
            selecting=False,
        )
        await conn.execute(
            quote_items.update()
            .where(quote_items.c.quote_item_id == item["quote_item_id"])
            .values(quantity=args.quantity, fulfillment_status=fulfillment)
        )
    return {
        "product_id": args.product_id,
        "quote_item_id": item["quote_item_id"],
        "quantity": args.quantity,
        "status": "removed" if args.quantity == 0 else "active",
    }


async def _replace(conn, args, ctx):
    if args.from_product_id == args.to_product_id:
        fail("INVALID_ALTERNATIVE", "Kaynak ve hedef ürün aynı olamaz.")
    source = await active_item(conn, ctx.quote_id, args.from_product_id)
    if source is None:
        fail("QUOTE_ITEM_NOT_FOUND", "Değiştirilecek aktif kalem bulunamadı.")
    source_product = product(ctx, args.from_product_id)
    target = product(ctx, args.to_product_id)
    if args.to_product_id not in source_product["substitute_product_ids"]:
        fail("INVALID_ALTERNATIVE", "Hedef ürün kayıtlı alternatifler arasında değil.")
    target_item = await active_item(conn, ctx.quote_id, args.to_product_id)
    quantity = (args.quantity if args.quantity is not None else source["quantity"]) + (
        target_item["quantity"] if target_item else 0
    )
    fulfillment = guard(
        ctx,
        target,
        quantity,
        snapshot=target_item["unit_price_try"] if target_item else None,
        replace=True,
    )
    target_id = target_item["quote_item_id"] if target_item else "QI-" + uuid4().hex
    if target_item:
        await conn.execute(
            quote_items.update()
            .where(quote_items.c.quote_item_id == target_id)
            .values(quantity=quantity, fulfillment_status=fulfillment)
        )
    else:
        await conn.execute(
            quote_items.insert().values(
                quote_item_id=target_id,
                quote_id=ctx.quote_id,
                product_id=args.to_product_id,
                quantity=quantity,
                unit_price_try=target["price_try"],
                status="active",
                fulfillment_status=fulfillment,
                source_message_id=ctx.message_id,
                idempotency_key=args.idempotency_key,
            )
        )
    await conn.execute(
        quote_items.update()
        .where(quote_items.c.quote_item_id == source["quote_item_id"])
        .values(status="replaced", replaced_by=target_id)
    )
    lost = sorted(set(source_product["tags"]) - set(target["tags"]))
    return {
        "from_product_id": args.from_product_id,
        "product_id": args.to_product_id,
        "quote_item_id": target_id,
        "quantity": quantity,
        "lost_features": lost,
        "reason": args.reason,
    }


async def receipt_operation(conn, args, ctx, tool_name, operation):
    if args.quote_id != ctx.quote_id:
        fail("QUOTE_CONTEXT_MISMATCH", "İstek teklif bağlamıyla eşleşmiyor.")
    key = action_key(ctx.quote_id, ctx.message_id, ctx.action_index, tool_name)
    if hasattr(args, "idempotency_key") and args.idempotency_key != key:
        fail("IDEMPOTENCY_CONFLICT", "İşlem anahtarı sunucu planıyla eşleşmiyor.")
    if isinstance(args, AddInput) and args.source_message_id != ctx.message_id:
        fail("QUOTE_CONTEXT_MISMATCH", "Kaynak mesaj bağlamıyla eşleşmiyor.")
    hashed = payload_hash(
        {
            "operation": tool_name,
            "arguments": args.model_dump(mode="json"),
            "constraints": ctx.constraints.model_dump(mode="json"),
            "session_id": ctx.session_id,
            "customer_id": ctx.customer_id,
        }
    )
    receipt = (
        (
            await conn.execute(
                sa.select(mutation_receipts).where(
                    mutation_receipts.c.quote_id == ctx.quote_id,
                    mutation_receipts.c.idempotency_key == key,
                )
            )
        )
        .mappings()
        .one_or_none()
    )
    if receipt:
        if receipt["payload_hash"] != hashed:
            fail("IDEMPOTENCY_CONFLICT", "Aynı anahtar farklı işlem içeriğiyle kullanıldı.")
        return {**receipt["result"], "replayed": True, "mutation_applied": False}
    before = (await get_quote(conn, ctx.quote_id)).model_dump(mode="json")
    # The executor holds the quote lock. Replay above remains valid even if the
    # quote has since changed or left draft; only new effects need these guards.
    if before["status"] != "draft":
        raise DomainError("QUOTE_NOT_EDITABLE", "Yalnız taslak teklif değiştirilebilir.", 409)
    if ctx.expected_quote_version is not None and before["version"] != ctx.expected_quote_version:
        raise DomainError(
            "QUOTE_VERSION_CONFLICT",
            "Teklif değişti. Güncel miktarı kontrol edip hedefini yeni mesajla gönder.",
            409,
        )
    delta = await operation(conn, args, ctx)
    version = await conn.scalar(
        quotes.update()
        .where(quotes.c.quote_id == ctx.quote_id)
        .values(version=quotes.c.version + 1)
        .returning(quotes.c.version)
    )
    after = (await get_quote(conn, ctx.quote_id)).model_dump(mode="json")
    result = {
        "operation": tool_name,
        "idempotency_key": key,
        "committed_version": version,
        "delta": delta,
        "replayed": False,
        "mutation_applied": True,
    }
    await conn.execute(
        mutation_receipts.insert().values(
            quote_id=ctx.quote_id,
            idempotency_key=key,
            session_id=ctx.session_id,
            message_id=ctx.message_id,
            action_index=ctx.action_index,
            operation=tool_name,
            payload_hash=hashed,
            before=before,
            after=after,
            result=result,
            committed_version=version,
        )
    )
    return result


async def add_to_quote(conn, args: AddInput, context):
    return await receipt_operation(conn, args, context, "add_to_quote", _add)


async def update_quote_item(conn, args: UpdateInput, context):
    return await receipt_operation(conn, args, context, "update_quote_item", _update)


async def replace_with_alternative(conn, args: ReplaceInput, context):
    return await receipt_operation(conn, args, context, "replace_with_alternative", _replace)
