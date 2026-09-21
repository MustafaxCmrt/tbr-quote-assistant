"""F01a: DB'siz liveness ve açıkça etkinleştirilen debug aktarım testi."""

import asyncio
import json
import os
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


def create_app() -> FastAPI:
    app = FastAPI(title="The Blue Red Teklif Asistanı", version="0.1.0")

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
