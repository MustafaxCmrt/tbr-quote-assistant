"""Liveness, PostgreSQL readiness and opt-in debug streaming."""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.reads import router as reads_router
from app.persistence.database import make_engine
from app.persistence.readiness import is_ready
from app.services.errors import DomainError

# Largest schema-valid admin record is well below this; bodies are buffered before validation.
MAX_BODY_BYTES = 256 * 1024
TOO_LARGE = {
    "code": "PAYLOAD_TOO_LARGE",
    "detail": "İstek gövdesi çok büyük; içeriği kısaltıp tekrar dene.",
}


class PayloadTooLarge(HTTPException):
    # FastAPI re-raises HTTPException from body parsing; other errors become a generic 400.
    def __init__(self):
        super().__init__(status_code=413)


def limit_body(app):
    async def guarded(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > MAX_BODY_BYTES):
            return await JSONResponse(status_code=413, content={"error": TOO_LARGE})(
                scope, receive, send
            )
        received = 0

        async def counted():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                # Chunked uploads carry no Content-Length; count what actually arrives.
                received += len(message.get("body", b""))
                if received > MAX_BODY_BYTES:
                    raise PayloadTooLarge()
            return message

        return await app(scope, counted, send)

    return guarded


def create_app(engine=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        owned = engine is None and bool(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DB"))
        app.state.engine = make_engine() if owned else engine
        try:
            yield
        finally:
            if owned:
                await app.state.engine.dispose()

    app = FastAPI(title="The Blue Red Teklif Asistanı", version="0.1.0", lifespan=lifespan)

    app.include_router(reads_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.add_middleware(limit_body)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code, "detail": exc.detail}}
        )

    @app.exception_handler(PayloadTooLarge)
    async def payload_too_large(request: Request, exc: PayloadTooLarge):
        return JSONResponse(status_code=413, content={"error": TOO_LARGE})

    @app.get("/health/ready", tags=["Sağlık"])
    async def ready():
        if await is_ready(app.state.engine):
            return {"status": "ready"}
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "Veritabanı henüz hazır değil."},
        )

    @app.get("/health/live", tags=["Sağlık"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    # Startup opt-in: unset/false/unknown values leave the route unregistered.
    if os.getenv("DEBUG_STREAM_SMOKE", "").lower() in {"1", "true"}:

        @app.post(
            "/api/debug/stream-smoke",
            tags=["DEBUG — geçici bağlantı testi"],
            summary="DB ve tool kullanmadan SSE bağlantısını dene",
            response_class=StreamingResponse,
            responses={200: {"content": {"text/event-stream": {}}}},
        )
        async def stream_smoke() -> StreamingResponse:
            async def events() -> AsyncIterator[str]:
                for seq, message in enumerate(
                    ["Bağlantı çalışıyor ğüşiöç", "İkinci parça ulaştı: ĞÜŞİÖÇ"],
                    start=1,
                ):
                    payload = json.dumps(
                        {"debug": True, "event_seq": seq, "text": message},
                        ensure_ascii=False,
                    )
                    yield f"event: text_delta\ndata: {payload}\n\n"
                    await asyncio.sleep(1)
                yield 'event: done\ndata: {"debug":true,"event_seq":3}\n\n'

            return StreamingResponse(
                events(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
            )

    return app


app = create_app()
