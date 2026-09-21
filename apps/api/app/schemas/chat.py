from typing import Literal

from pydantic import Field

from app.schemas.tools import DTO


class SessionInput(DTO):
    customer_id: str = Field(min_length=1, max_length=100)
    quote_id: str = Field(min_length=1, max_length=100)
    channel: Literal["web", "mobile"] = "web"
    locale: Literal["tr"] = "tr"


class ChatInput(DTO):
    session_id: str = Field(min_length=1, max_length=100)
    message_id: str = Field(min_length=1, max_length=100)
    quote_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)
    channel: Literal["web", "mobile"] = "web"
    locale: Literal["tr"] = "tr"
