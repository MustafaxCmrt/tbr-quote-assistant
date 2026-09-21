import json
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from pydantic import Field

from app.schemas.tools import DTO


class Constraints(DTO):
    max_price_try: Decimal | None = Field(default=None, ge=0)
    required_tags: list[str] = Field(default_factory=list)
    explicit_backorder_consent: bool = False
    explicit_plus: bool = False


@dataclass(frozen=True)
class ExecutionContext:
    session_id: str
    message_id: str
    attempt_id: str
    quote_id: str
    customer_id: str
    action_index: int
    constraints: Constraints
    customer: dict
    catalog: dict
    expected_quote_version: int | None = None


def action_key(quote_id, message_id, index, tool_name):
    return sha256(
        json.dumps([quote_id, message_id, index, tool_name], separators=(",", ":")).encode()
    ).hexdigest()


def payload_hash(value):
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
