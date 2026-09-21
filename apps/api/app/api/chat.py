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
