from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from app.schemas.tools import DTO
from app.services.evidence import Source

ToolName = Literal[
    "search_products",
    "get_knowledge_entries",
    "get_quote",
    "add_to_quote",
    "update_quote_item",
    "replace_with_alternative",
]


class StartPayload(DTO):
    mode: Literal["fallback", "deterministic"]


class ToolStartPayload(DTO):
    name: ToolName
    input: dict
    tool_sequence: int = Field(ge=1)
    action_index: int = Field(ge=0)


class ToolResultPayload(DTO):
    name: ToolName
    tool_sequence: int = Field(ge=1)
    success: bool
    output: dict
    sources: list[Source]
    replayed: bool
    mutation_applied: bool


class SourcesPayload(DTO):
    sources: list[Source]


class TextPayload(DTO):
    text: str


class DonePayload(DTO):
    success: Literal[True] = True
    quote_id: str
    quote_version: int
    mode: Literal["fallback", "deterministic"]
    source_ids: list[str]


class ErrorPayload(DTO):
    code: str
    detail: str
    retryable: bool
    committed: bool
    quote_id: str


class Envelope(DTO):
    schema_version: Literal[1] = 1
    session_id: str
    message_id: str
    attempt_id: str
    event_seq: int = Field(ge=1)


class MessageStart(Envelope):
    type: Literal["message_start"]
    payload: StartPayload


class ToolStart(Envelope):
    type: Literal["tool_call_start"]
    payload: ToolStartPayload


class ToolResult(Envelope):
    type: Literal["tool_call_result"]
    payload: ToolResultPayload


class Sources(Envelope):
    type: Literal["sources"]
    payload: SourcesPayload


class Text(Envelope):
    type: Literal["text_delta"]
    payload: TextPayload


class Done(Envelope):
    type: Literal["done"]
    payload: DonePayload


class Error(Envelope):
    type: Literal["error"]
    payload: ErrorPayload


StreamEvent = Annotated[
    MessageStart | ToolStart | ToolResult | Sources | Text | Done | Error,
    Field(discriminator="type"),
]
stream_adapter = TypeAdapter(StreamEvent)
