from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

Money = Annotated[
    Decimal, PlainSerializer(lambda value: format(value, ".2f"), return_type=str, when_used="json")
]


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProductFilters(DTO):
    category: str | None = None
    max_price_try: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    in_stock_only: bool = True
    required_tags: list[str] = Field(default_factory=list, max_length=30)


class ProductSearchInput(DTO):
    query: str = Field(max_length=2000)
    locale: Literal["tr"] = "tr"
    filters: ProductFilters = Field(default_factory=ProductFilters)
    limit: int = Field(default=10, ge=1, le=50)


class KnowledgeInput(DTO):
    query: str = Field(max_length=2000)
    locale: Literal["tr"] = "tr"
    topic: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class GetQuoteInput(DTO):
    quote_id: str = Field(min_length=1, max_length=100)


class ProductMatch(DTO):
    product_id: str
    sku: str
    name_tr: str
    price_try: Money
    stock_qty: int
    category: str
    tags: list[str]
    substitute_product_ids: list[str]
    match_evidence: list[str]


class ProductSearchResult(DTO):
    recommendations: list[ProductMatch]
    unavailable_matches: list[ProductMatch]
    applied_filters: ProductFilters


class KnowledgeEntry(DTO):
    knowledge_id: str
    topic: str
    title: str
    body: str
    source: str


class KnowledgeResult(DTO):
    entries: list[KnowledgeEntry]


class QuoteLine(DTO):
    quote_item_id: str
    product_id: str
    sku: str
    name_tr: str
    quantity: int
    unit_price_try: Money
    gross_total_try: Money
    discount_total_try: Money
    net_total_try: Money
    rule_ids: list[str]
    status: str
    fulfillment_status: str
    replaced_by: str | None


class QuoteDTO(DTO):
    quote_id: str
    customer_id: str
    customer_name: str
    status: str
    currency: str
    version: int
    items: list[QuoteLine]
    history: list[QuoteLine]
    gross_total_try: Money
    discount_total_try: Money
    net_total_try: Money
    rule_ids: list[str]
