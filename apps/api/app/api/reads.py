from fastapi import APIRouter, Request

from app.persistence.readiness import is_ready
from app.schemas.tools import (
    KnowledgeInput,
    KnowledgeResult,
    ProductSearchInput,
    ProductSearchResult,
    QuoteDTO,
)
from app.services.errors import DomainError
from app.services.quotes import get_quote
from app.services.retrieval import get_knowledge_entries, search_products

router = APIRouter(prefix="/api")


async def engine_for(request):
    engine = request.app.state.engine
    if not await is_ready(engine):
        raise DomainError("NOT_READY", "Veritabanı henüz hazır değil.", 503)
    return engine


@router.post("/tools/search_products", response_model=ProductSearchResult, tags=["Okuma araçları"])
async def products(args: ProductSearchInput, request: Request):
    engine = await engine_for(request)
    async with engine.connect() as connection:
        return await search_products(connection, args)


@router.post(
    "/tools/get_knowledge_entries", response_model=KnowledgeResult, tags=["Okuma araçları"]
)
async def knowledge(args: KnowledgeInput, request: Request):
    engine = await engine_for(request)
    async with engine.connect() as connection:
        return await get_knowledge_entries(connection, args)


@router.get("/quotes/{quote_id}", response_model=QuoteDTO, tags=["Teklifler"])
async def quote(quote_id: str, request: Request):
    engine = await engine_for(request)
    # Multiple selects must describe one committed version, not mix concurrent states.
    async with engine.connect() as connection:
        connection = await connection.execution_options(isolation_level="REPEATABLE READ")
        async with connection.begin():
            return await get_quote(connection, quote_id)
