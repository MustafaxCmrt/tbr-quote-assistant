"""One short PostgreSQL transaction per persisted tool plan; no network/provider work."""

from time import perf_counter
from uuid import uuid4

import sqlalchemy as sa
from pydantic import ValidationError

from app.persistence.models import (
    chat_messages,
    chat_sessions,
    customers,
    price_rules,
    products,
    quote_items,
    quotes,
    tool_call_logs,
)
from app.schemas.tools import (
    AddInput,
    GetQuoteInput,
    KnowledgeInput,
    ProductSearchInput,
    ReplaceInput,
    UpdateInput,
)
from app.services.errors import DomainError
from app.services.evidence import EvidenceBundle
from app.services.execution_context import Constraints, ExecutionContext
from app.services.mutations import add_to_quote, replace_with_alternative, update_quote_item
from app.services.quotes import get_quote
from app.services.retrieval import get_knowledge_entries, search_products

MUTATIONS = {
    "add_to_quote": (AddInput, add_to_quote),
    "update_quote_item": (UpdateInput, update_quote_item),
    "replace_with_alternative": (ReplaceInput, replace_with_alternative),
}
SCHEMAS = {
    **{name: pair[0] for name, pair in MUTATIONS.items()},
    "search_products": ProductSearchInput,
    "get_knowledge_entries": KnowledgeInput,
    "get_quote": GetQuoteInput,
}


async def execute_plan(engine, session_id, message_id, *, attempt_id=None):
    attempt_id = attempt_id or uuid4().hex
    async with engine.begin() as conn:
        session = (
            (
                await conn.execute(
                    sa.select(chat_sessions).where(chat_sessions.c.session_id == session_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if session is None:
            raise DomainError("QUOTE_CONTEXT_MISMATCH", "Oturum bulunamadı.", 404)
        # Quote lock is the receipt claim serialization point, including concurrent new keys.
        quote = (
            (
                await conn.execute(
                    sa.select(quotes)
                    .where(quotes.c.quote_id == session["quote_id"])
                    .with_for_update()
                )
            )
            .mappings()
            .one()
        )
        if quote["customer_id"] != session["customer_id"]:
            raise DomainError("QUOTE_CONTEXT_MISMATCH", "Müşteri ve teklif eşleşmiyor.")
        message = (
            (
                await conn.execute(
                    sa.select(chat_messages)
                    .where(
                        chat_messages.c.session_id == session_id,
                        chat_messages.c.message_id == message_id,
                    )
                    .with_for_update()
                )
            )
            .mappings()
            .one_or_none()
        )
        if message is None:
            raise DomainError("MESSAGE_NOT_FOUND", "Mesaj bulunamadı.", 404)
        plan = message["persisted_plan"]
        try:
            constraints = Constraints.model_validate(message["trusted_constraints"])
            parsed = [
                (step["name"], SCHEMAS[step["name"]].model_validate(step["arguments"]))
                for step in plan
            ]
        except (ValidationError, KeyError, TypeError) as error:
            raise DomainError("INVALID_INPUT", "Kayıtlı işlem planı geçersiz.") from error
        if any(
            getattr(args, "quote_id", quote["quote_id"]) != quote["quote_id"] for _, args in parsed
        ):
            raise DomainError("QUOTE_CONTEXT_MISMATCH", "İşlem başka teklife erişemez.")
        customer = dict(
            (
                await conn.execute(
                    sa.select(customers)
                    .where(customers.c.customer_id == session["customer_id"])
                    .with_for_update(read=True)
                )
            )
            .mappings()
            .one()
        )
        # Stable global product lock order prevents reversed two-product plans deadlocking.
        ids = set(
            (
                await conn.execute(
                    sa.select(quote_items.c.product_id).where(
                        quote_items.c.quote_id == quote["quote_id"]
                    )
                )
            ).scalars()
        )
        for _, args in parsed:
            for field in ("product_id", "from_product_id", "to_product_id"):
                value = getattr(args, field, None)
                if value:
                    ids.add(value)
        catalog = {
            row["product_id"]: dict(row)
            for row in (
                await conn.execute(
                    sa.select(products)
                    .where(products.c.product_id.in_(ids))
                    .order_by(products.c.product_id)
                    .with_for_update(read=True)
                )
            ).mappings()
        }
        # Pricing decisions stay stable until commit, even if admin updates rates concurrently.
        await conn.execute(
            sa.select(price_rules).order_by(price_rules.c.rule_id).with_for_update(read=True)
        )
        outputs = []
        for index, (name, args) in enumerate(parsed):
            started = perf_counter()
            context = ExecutionContext(
                session_id,
                message_id,
                attempt_id,
                quote["quote_id"],
                session["customer_id"],
                index,
                constraints.model_copy(
                    update={
                        "required_tags": sorted(
                            set(constraints.required_tags)
                            | set(plan[index].get("required_tags", []))
                        )
                    }
                ),
                customer,
                catalog,
            )
            if name in MUTATIONS:
                # Always invoke the actual wrapper, including receipt replay attempts.
                output = await MUTATIONS[name][1](conn, args, context)
                evidence = EvidenceBundle.from_results(await get_quote(conn, quote["quote_id"]))
            elif name == "search_products":
                result = await search_products(conn, args)
                output = result.model_dump(mode="json")
                evidence = EvidenceBundle.from_results(result)
            elif name == "get_knowledge_entries":
                result = await get_knowledge_entries(conn, args)
                output = result.model_dump(mode="json")
                evidence = EvidenceBundle.from_results(result)
            else:
                result = await get_quote(conn, args.quote_id)
                output = result.model_dump(mode="json")
                evidence = EvidenceBundle.from_results(result)
            await conn.execute(
                tool_call_logs.insert().values(
                    session_id=session_id,
                    message_id=message_id,
                    attempt_id=attempt_id,
                    tool_sequence=index + 1,
                    tool_name=name,
                    input=args.model_dump(mode="json"),
                    output=output,
                    sources=evidence.model_dump(mode="json")["sources"],
                    success=True,
                    replayed=output.get("replayed", False),
                    mutation_applied=output.get("mutation_applied", False),
                    duration_ms=int((perf_counter() - started) * 1000),
                )
            )
            outputs.append(output)
    # No successful result leaves this function before the enclosing transaction commits.
    return outputs
