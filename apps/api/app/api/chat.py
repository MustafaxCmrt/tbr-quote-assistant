from fastapi import APIRouter, Request

from app.api.reads import engine_for
from app.orchestration.chat import create_session, process_chat
from app.schemas.chat import ChatInput, SessionInput

router = APIRouter(prefix="/api", tags=["Sohbet"])


@router.post("/chat/sessions", status_code=201)
async def session(args: SessionInput, request: Request):
    return await create_session(await engine_for(request), args)


@router.post("/chat")
async def chat(args: ChatInput, request: Request):
    return await process_chat(await engine_for(request), args)


@router.post("/chat/stream")
async def stream(args: ChatInput, request: Request):
    from fastapi.responses import StreamingResponse

    from app.orchestration.streaming import stream_chat

    engine = await engine_for(request)
    await require_session(engine, args.session_id, args.quote_id)
    return StreamingResponse(
        stream_chat(engine, args),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


async def require_session(engine, session_id, quote_id=None):
    import sqlalchemy as sa

    from app.persistence.models import chat_sessions
    from app.services.errors import DomainError

    async with engine.connect() as conn:
        row = (
            (
                await conn.execute(
                    sa.select(chat_sessions).where(chat_sessions.c.session_id == session_id)
                )
            )
            .mappings()
            .one_or_none()
        )
    if row is None or (quote_id is not None and quote_id != row["quote_id"]):
        raise DomainError("QUOTE_CONTEXT_MISMATCH", "Oturum ve teklif eşleşmiyor.", 404)
    return row


@router.get("/chat/sessions/{session_id}/messages")
async def messages(session_id: str, request: Request):
    import sqlalchemy as sa

    from app.persistence.models import chat_messages

    engine = await engine_for(request)
    await require_session(engine, session_id)
    async with engine.connect() as conn:
        return (
            (
                await conn.execute(
                    sa.select(
                        chat_messages.c.message_id,
                        chat_messages.c.body,
                        chat_messages.c.status,
                        chat_messages.c.final_response,
                        chat_messages.c.created_at,
                    )
                    .where(chat_messages.c.session_id == session_id)
                    .order_by(chat_messages.c.created_at)
                    .limit(200)
                )
            )
            .mappings()
            .all()
        )


@router.get("/tool-calls")
async def tool_calls(session_id: str, request: Request):
    import sqlalchemy as sa

    from app.persistence.models import tool_call_logs

    engine = await engine_for(request)
    await require_session(engine, session_id)
    async with engine.connect() as conn:
        return (
            (
                await conn.execute(
                    sa.select(tool_call_logs)
                    .where(tool_call_logs.c.session_id == session_id)
                    .order_by(tool_call_logs.c.log_id)
                    .limit(500)
                )
            )
            .mappings()
            .all()
        )
