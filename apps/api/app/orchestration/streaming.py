"""Transport disconnect does not cancel an accepted DB plan. No transaction spans text chunks."""

import asyncio
import os
from uuid import uuid4

import sqlalchemy as sa

from app.orchestration.chat import process_chat
from app.persistence.models import mutation_receipts
from app.schemas.stream import stream_adapter
from app.services.errors import DomainError

# Strong references keep finite accepted tasks alive until DB/message completion.
ACTIVE_STREAMS = set()


async def stream_chat(engine, request):
    queue = asyncio.Queue()
    attempt = uuid4().hex
    sequence = 0

    def emit(kind, payload):
        nonlocal sequence
        sequence += 1
        event = stream_adapter.validate_python(
            {
                "type": kind,
                "payload": payload,
                "event_seq": sequence,
                "session_id": request.session_id,
                "message_id": request.message_id,
                "attempt_id": attempt,
            }
        )
        queue.put_nowait(f"event: {kind}\ndata: {event.model_dump_json()}\n\n")

    async def produce():
        mode = (
            "fallback"
            if os.getenv("LLM_MODE", "off") == "off" or not os.getenv("OPENAI_API_KEY", "").strip()
            else "deterministic"
        )
        emit("message_start", {"mode": mode})
        try:
            response = await process_chat(engine, request, attempt_id=attempt, on_event=emit)
            emit("sources", {"sources": response["sources"]})
            # Deliberately paced template delivery, not provider token generation.
            # Give native rendering time between frames; cap added delivery time at 4s.
            chunk_size = max(80, (len(response["text"]) + 79) // 80)
            for start in range(0, len(response["text"]), chunk_size):
                emit("text_delta", {"text": response["text"][start : start + chunk_size]})
                await asyncio.sleep(0.05)
            emit(
                "done",
                {
                    "success": True,
                    "quote_id": request.quote_id,
                    "quote_version": response["quote"]["version"],
                    "mode": response["mode"],
                    "source_ids": [s["source_id"] for s in response["sources"]],
                },
            )
        except Exception as exc:  # noqa: BLE001 -- transport boundary masks unexpected internals
            committed = False
            try:
                async with asyncio.timeout(3), engine.connect() as conn:
                    committed = bool(
                        await conn.scalar(
                            sa.select(sa.func.count())
                            .select_from(mutation_receipts)
                            .where(
                                mutation_receipts.c.session_id == request.session_id,
                                mutation_receipts.c.message_id == request.message_id,
                            )
                        )
                    )
            except Exception:  # noqa: BLE001 -- unreachable DB raises raw OSError/TimeoutError too
                # Uncertain commit state: refetch instead of telling a client nothing happened.
                # Any probe failure must still end the stream with the terminal error frame.
                committed = True
            emit(
                "error",
                {
                    "code": exc.code if isinstance(exc, DomainError) else "INTERNAL_ERROR",
                    "detail": exc.detail
                    if isinstance(exc, DomainError)
                    else "İşlem tamamlanamadı. Teklifi yenileyip aynı mesajla tekrar deneyebilirsin.",
                    "retryable": not isinstance(exc, DomainError)
                    or exc.code == "MESSAGE_IN_PROGRESS",
                    "committed": committed,
                    "quote_id": request.quote_id,
                },
            )
        finally:
            queue.put_nowait(None)

    task = asyncio.create_task(produce())
    ACTIVE_STREAMS.add(task)
    task.add_done_callback(ACTIVE_STREAMS.discard)
    while True:
        frame = await queue.get()
        if frame is None:
            break
        yield frame
