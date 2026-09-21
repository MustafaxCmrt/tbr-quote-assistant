from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, create_model

from app.schemas.tools import DTO, Money

Identifier = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{0,99}$")]
ShortText = Annotated[str, Field(min_length=1, max_length=200)]
Category = Literal[
    "barcode_scanner",
    "pos_terminal",
    "receipt_printer",
    "label_printer",
    "software",
    "accessory",
    "service",
    "bundle",
]


class ProductCreate(DTO):
    product_id: Identifier | None = None
    sku: ShortText
    name_tr: ShortText
    category: Category
    brand: ShortText
    price_try: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    stock_qty: int = Field(ge=0, le=100000000, strict=True)
    active: bool = True
    min_order_qty: int = Field(default=1, ge=1, le=1000000, strict=True)
    delivery_days: int = Field(default=0, ge=0, le=3650, strict=True)
    warranty_months: int = Field(default=0, ge=0, le=1200, strict=True)
    tags: list[ShortText] = Field(default_factory=list, max_length=30)
    aliases: dict[Literal["tr"], list[ShortText]] = Field(
        default_factory=lambda: {"tr": []}, max_length=1
    )
    substitute_product_ids: list[Identifier] = Field(default_factory=list, max_length=30)
    notes: str = Field(default="", max_length=4000)


class ProductRecord(ProductCreate):
    product_id: Identifier
    price_try: Money


class KnowledgeCreate(DTO):
    knowledge_id: Identifier | None = None
    topic: ShortText
    locale: Literal["tr"] = "tr"
    title: ShortText
    body: str = Field(min_length=1, max_length=12000)
    source: str = Field(min_length=1, max_length=500)
    effective_from: date
    active: bool = True
    applies_to: list[ShortText] = Field(default_factory=list, max_length=50)


class KnowledgeRecord(KnowledgeCreate):
    knowledge_id: Identifier


def patch_model(name, model, id_field):
    # Preserve each field's bounds, but allow omission; explicit null is rejected by the route.
    return create_model(
        name,
        __base__=DTO,
        **{
            key: (
                Annotated[field.annotation | None, *field.metadata]
                if field.metadata
                else field.annotation | None,
                None,
            )
            for key, field in model.model_fields.items()
            if key != id_field
        },
    )


ProductPatch = patch_model("ProductPatch", ProductCreate, "product_id")
KnowledgePatch = patch_model("KnowledgePatch", KnowledgeCreate, "knowledge_id")
