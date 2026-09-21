from decimal import Decimal

import sqlalchemy as sa

from app.persistence.models import customers, price_rules, products, quote_items, quotes
from app.schemas.tools import QuoteDTO, QuoteLine
from app.services.errors import DomainError
from app.services.pricing import amount, price_lines


async def get_quote(connection, quote_id: str) -> QuoteDTO:
    quote = (
        (await connection.execute(sa.select(quotes).where(quotes.c.quote_id == quote_id)))
        .mappings()
        .one_or_none()
    )
    if quote is None:
        raise DomainError("QUOTE_NOT_FOUND", "Teklif bulunamadı.", 404)
    customer = (
        (
            await connection.execute(
                sa.select(customers).where(customers.c.customer_id == quote["customer_id"])
            )
        )
        .mappings()
        .one()
    )
    items = (
        (
            await connection.execute(
                sa.select(quote_items)
                .where(quote_items.c.quote_id == quote_id)
                .order_by(quote_items.c.quote_item_id)
            )
        )
        .mappings()
        .all()
    )
    ids = [item["product_id"] for item in items]
    catalog = (
        (await connection.execute(sa.select(products).where(products.c.product_id.in_(ids))))
        .mappings()
        .all()
    )
    by_id = {p["product_id"]: p for p in catalog}
    rules = (await connection.execute(sa.select(price_rules))).mappings().all()
    totals = price_lines(items, by_id, customer, rules)
    lines = [
        QuoteLine(
            **{
                k: item[k]
                for k in (
                    "quote_item_id",
                    "product_id",
                    "quantity",
                    "unit_price_try",
                    "status",
                    "fulfillment_status",
                    "replaced_by",
                )
            },
            sku=by_id[item["product_id"]]["sku"],
            name_tr=by_id[item["product_id"]]["name_tr"],
            **totals[item["quote_item_id"]],
        )
        for item in items
    ]
    active = [line for line in lines if line.status == "active"]
    return QuoteDTO(
        **{key: quote[key] for key in ("quote_id", "customer_id", "status", "currency", "version")},
        customer_name=customer["name"],
        items=active,
        history=[line for line in lines if line.status != "active"],
        gross_total_try=amount(sum((line.gross_total_try for line in active), Decimal(0))),
        discount_total_try=amount(sum((line.discount_total_try for line in active), Decimal(0))),
        net_total_try=amount(sum((line.net_total_try for line in active), Decimal(0))),
        rule_ids=sorted({rule for line in active for rule in line.rule_ids}),
    )
