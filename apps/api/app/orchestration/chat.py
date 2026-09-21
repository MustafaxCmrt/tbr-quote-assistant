"""Persist intent before execution. Retry invokes real tools and committed receipts."""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import sqlalchemy as sa

from app.orchestration.planner import build_plan
from app.orchestration.templates import render
from app.persistence.models import chat_messages, chat_sessions, quotes, tool_call_logs
from app.services.errors import DomainError
from app.services.execution_context import payload_hash
from app.services.executor import execute_plan


async def create_session(engine, request):
    async with engine.begin() as conn:
        quote = (
            (await conn.execute(sa.select(quotes).where(quotes.c.quote_id == request.quote_id)))
            .mappings()
            .one_or_none()
        )
        if quote is None or quote["customer_id"] != request.customer_id:
            raise DomainError("QUOTE_CONTEXT_MISMATCH", "Müşteri ve teklif eşleşmiyor.", 404)
        values = dict(session_id=uuid4().hex, **request.model_dump())
        await conn.execute(chat_sessions.insert().values(**values))
    return values


async def process_chat(engine, request, *, attempt_id=None, on_event=None):
    attempt_id = attempt_id or uuid4().hex
    mode = (
        "fallback"
        if os.getenv("LLM_MODE", "off") == "off" or not os.getenv("OPENAI_API_KEY", "").strip()
        else "deterministic"
    )
    # No provider adapter exists in this deterministic delivery. Environment cannot enable spending.
    signature = payload_hash(
        {"message": request.message, "quote_id": request.quote_id, "locale": request.locale}
    )
    message_filter = (
        chat_messages.c.session_id == request.session_id,
        chat_messages.c.message_id == request.message_id,
    )
    async with engine.begin() as conn:
        session = (
            (
                await conn.execute(
                    sa.select(chat_sessions).where(chat_sessions.c.session_id == request.session_id)
                )
            )
            .mappings()
            .one_or_none()
        )
        if session is None or session["quote_id"] != request.quote_id:
            raise DomainError("QUOTE_CONTEXT_MISMATCH", "Oturum ve teklif eşleşmiyor.", 404)
        # Same order as executor: quote then message. DB lock, not process-local mutex.
        await conn.execute(
            sa.select(quotes.c.quote_id)
            .where(quotes.c.quote_id == session["quote_id"])
            .with_for_update()
        )
        existing = (
            (await conn.execute(sa.select(chat_messages).where(*message_filter).with_for_update()))
            .mappings()
            .one_or_none()
        )
        now = datetime.now(UTC)
        if existing:
            if existing["payload_hash"] != signature:
                raise DomainError(
                    "IDEMPOTENCY_CONFLICT", "Aynı mesaj kimliği farklı içerikle kullanılamaz.", 409
                )
            if (
                existing["status"] == "processing"
                and existing["lease_until"]
                and existing["lease_until"] > now
            ):
                raise DomainError(
                    "MESSAGE_IN_PROGRESS",
                    "Mesaj işleniyor; aynı kimlikle tekrar deneyebilirsin.",
                    409,
                )
            notice = (existing["final_response"] or {}).get("notice", "")
            await conn.execute(
                chat_messages.update()
                .where(*message_filter)
                .values(status="processing", lease_until=now + timedelta(seconds=60))
            )
        else:
            plan = await build_plan(conn, session, request.message_id, request.message, mode)
            notice = plan.notice
            await conn.execute(
                chat_messages.insert().values(
                    session_id=request.session_id,
                    message_id=request.message_id,
                    body=request.message,
                    payload_hash=signature,
                    persisted_plan=plan.steps,
                    trusted_constraints=plan.constraints.model_dump(mode="json"),
                    status="processing",
                    lease_until=now + timedelta(seconds=60),
                    final_response={"notice": notice},
                )
            )
    try:
        await execute_plan(
            engine, request.session_id, request.message_id, attempt_id=attempt_id, on_event=on_event
        )
        async with engine.begin() as conn:
            logs = (
                (
                    await conn.execute(
                        sa.select(tool_call_logs)
                        .where(
                            tool_call_logs.c.session_id == request.session_id,
                            tool_call_logs.c.message_id == request.message_id,
                            tool_call_logs.c.attempt_id == attempt_id,
                        )
                        .order_by(tool_call_logs.c.tool_sequence)
                    )
                )
                .mappings()
                .all()
            )
            response = dict(
                session_id=request.session_id,
                message_id=request.message_id,
                attempt_id=attempt_id,
                mode=mode,
                provider_calls=0,
                notice=notice,
                **render(logs, notice, mode),
            )
            await conn.execute(
                chat_messages.update()
                .where(*message_filter)
                .values(status="completed", lease_until=None, final_response=response)
            )
        return response
    except Exception as exc:
        async with engine.begin() as conn:
            failed = getattr(exc, "tool_failure", None)
            if failed:
                code = exc.code if isinstance(exc, DomainError) else "INTERNAL_ERROR"
                await conn.execute(
                    tool_call_logs.insert().values(
                        session_id=request.session_id,
                        message_id=request.message_id,
                        attempt_id=attempt_id,
                        **failed,
                        output={"error": {"code": code}},
                        sources=[],
                        success=False,
                        replayed=False,
                        mutation_applied=False,
                    )
                )
            await conn.execute(
                chat_messages.update()
                .where(*message_filter)
                .values(status="failed", lease_until=None)
            )
        raise
