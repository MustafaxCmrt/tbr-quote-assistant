from uuid import uuid4

import sqlalchemy as sa
from fastapi import APIRouter, Query, Request, Response
from sqlalchemy.exc import IntegrityError

from app.api.reads import engine_for
from app.persistence.models import chat_sessions, customers, knowledge_entries, products, quotes
from app.schemas.admin import (
    KnowledgeCreate,
    KnowledgePatch,
    KnowledgeRecord,
    ProductCreate,
    ProductPatch,
    ProductRecord,
)
from app.services.errors import DomainError

router = APIRouter(prefix="/api", tags=["Yönetim"])


async def one(engine, table, id_field, identifier):
    async with engine.connect() as conn:
        row = (
            (await conn.execute(sa.select(table).where(table.c[id_field] == identifier)))
            .mappings()
            .one_or_none()
        )
    if row is None:
        raise DomainError("NOT_FOUND", "Kayıt bulunamadı.", 404)
    return row


async def write(engine, table, id_field, values, identifier=None):
    if any(v is None for v in values.values()):
        raise DomainError(
            "INVALID_INPUT", "Alanlar null olamaz; değiştirmediğin alanları gönderme."
        )
    try:
        async with engine.begin() as conn:
            if identifier is not None:
                current = (
                    (
                        await conn.execute(
                            sa.select(table)
                            .where(table.c[id_field] == identifier)
                            .with_for_update()
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if current is None:
                    raise DomainError("NOT_FOUND", "Kayıt bulunamadı.", 404)
            else:
                values[id_field] = (
                    values.get(id_field)
                    or ("PRD-" if table is products else "KNE-") + uuid4().hex[:16].upper()
                )
            if table is products and "substitute_product_ids" in values:
                alternatives = set(values["substitute_product_ids"])
                found = set(
                    (
                        await conn.execute(
                            sa.select(products.c.product_id).where(
                                products.c.product_id.in_(alternatives)
                            )
                        )
                    ).scalars()
                )
                if found != alternatives or (identifier or values[id_field]) in alternatives:
                    raise DomainError(
                        "INVALID_INPUT", "Alternatif ürünler mevcut ve farklı kayıtlar olmalı."
                    )
            if identifier is None:
                row = (
                    (await conn.execute(table.insert().values(**values).returning(table)))
                    .mappings()
                    .one()
                )
            else:
                row = (
                    (
                        await conn.execute(
                            table.update()
                            .where(table.c[id_field] == identifier)
                            .values(**values)
                            .returning(table)
                        )
                    )
                    .mappings()
                    .one()
                )
        return row
    except IntegrityError as exc:
        raise DomainError(
            "CONFLICT", "Bu kimlik veya SKU zaten kayıtlı; farklı bir değer kullan.", 409
        ) from exc


@router.get("/products")
async def list_products(
    request: Request,
    query: str = "",
    category: str | None = None,
    in_stock_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_inactive: bool = False,
):
    engine = await engine_for(request)
    filters = [] if include_inactive else [products.c.active.is_(True)]
    if query:
        filters.append(
            sa.or_(
                products.c.name_tr.ilike("%" + query + "%"), products.c.sku.ilike("%" + query + "%")
            )
        )
    if category:
        filters.append(products.c.category == category)
    if in_stock_only:
        filters.append(products.c.stock_qty > 0)
    async with engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    sa.select(products)
                    .where(*filters)
                    .order_by(products.c.product_id)
                    .limit(limit)
                    .offset(offset)
                )
            )
            .mappings()
            .all()
        )
        total = await conn.scalar(sa.select(sa.func.count()).select_from(products).where(*filters))
    return {
        "items": [ProductRecord.model_validate(r).model_dump(mode="json") for r in rows],
        "total": total,
    }


@router.post("/products", status_code=201, response_model=ProductRecord)
async def create_product(args: ProductCreate, request: Request):
    return await write(
        await engine_for(request), products, "product_id", args.model_dump(exclude_none=True)
    )


@router.get("/products/{identifier}", response_model=ProductRecord)
async def product(identifier: str, request: Request):
    return await one(await engine_for(request), products, "product_id", identifier)


@router.patch("/products/{identifier}", response_model=ProductRecord)
async def update_product(identifier: str, args: ProductPatch, request: Request):
    values = args.model_dump(exclude_unset=True)
    if not values:
        raise DomainError("INVALID_INPUT", "Değiştirilecek alan gönderilmedi.")
    return await write(await engine_for(request), products, "product_id", values, identifier)


@router.delete("/products/{identifier}", status_code=204)
async def delete_product(identifier: str, request: Request):
    await write(await engine_for(request), products, "product_id", {"active": False}, identifier)
    return Response(status_code=204)


@router.get("/knowledge")
async def list_knowledge(
    request: Request,
    query: str = "",
    topic: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_inactive: bool = False,
):
    engine = await engine_for(request)
    filters = [] if include_inactive else [knowledge_entries.c.active.is_(True)]
    if topic:
        filters.append(knowledge_entries.c.topic == topic)
    if query:
        filters.append(knowledge_entries.c.title.ilike("%" + query + "%"))
    async with engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    sa.select(knowledge_entries)
                    .where(*filters)
                    .order_by(knowledge_entries.c.knowledge_id)
                    .limit(limit)
                    .offset(offset)
                )
            )
            .mappings()
            .all()
        )
        total = await conn.scalar(
            sa.select(sa.func.count()).select_from(knowledge_entries).where(*filters)
        )
    return {
        "items": [KnowledgeRecord.model_validate(r).model_dump(mode="json") for r in rows],
        "total": total,
    }


@router.post("/knowledge", status_code=201, response_model=KnowledgeRecord)
async def create_knowledge(args: KnowledgeCreate, request: Request):
    return await write(
        await engine_for(request),
        knowledge_entries,
        "knowledge_id",
        args.model_dump(exclude_none=True),
    )


@router.get("/knowledge/{identifier}", response_model=KnowledgeRecord)
async def knowledge(identifier: str, request: Request):
    return await one(await engine_for(request), knowledge_entries, "knowledge_id", identifier)


@router.patch("/knowledge/{identifier}", response_model=KnowledgeRecord)
async def update_knowledge(identifier: str, args: KnowledgePatch, request: Request):
    values = args.model_dump(exclude_unset=True)
    if not values:
        raise DomainError("INVALID_INPUT", "Değiştirilecek alan gönderilmedi.")
    return await write(
        await engine_for(request), knowledge_entries, "knowledge_id", values, identifier
    )


@router.delete("/knowledge/{identifier}", status_code=204)
async def delete_knowledge(identifier: str, request: Request):
    await write(
        await engine_for(request), knowledge_entries, "knowledge_id", {"active": False}, identifier
    )
    return Response(status_code=204)


@router.get("/customers")
async def list_customers(request: Request):
    engine = await engine_for(request)
    async with engine.connect() as conn:
        return (
            (
                await conn.execute(
                    sa.select(
                        customers.c.customer_id,
                        customers.c.name,
                        customers.c.city,
                        customers.c.price_tier,
                    ).order_by(customers.c.customer_id)
                )
            )
            .mappings()
            .all()
        )


@router.get("/quotes")
async def list_quotes(customer_id: str, request: Request):
    engine = await engine_for(request)
    async with engine.connect() as conn:
        return (
            (
                await conn.execute(
                    sa.select(
                        quotes.c.quote_id, quotes.c.customer_id, quotes.c.status, quotes.c.version
                    )
                    .where(quotes.c.customer_id == customer_id)
                    .order_by(quotes.c.quote_id)
                )
            )
            .mappings()
            .all()
        )


@router.get("/chat/sessions")
async def list_sessions(request: Request, quote_id: str):
    engine = await engine_for(request)
    async with engine.connect() as conn:
        return (
            (
                await conn.execute(
                    sa.select(chat_sessions)
                    .where(chat_sessions.c.quote_id == quote_id)
                    .order_by(chat_sessions.c.created_at.desc())
                    .limit(100)
                )
            )
            .mappings()
            .all()
        )
