import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from app.persistence.models import knowledge_entries, products
from app.schemas.tools import (
    KnowledgeEntry,
    KnowledgeInput,
    KnowledgeResult,
    ProductMatch,
    ProductSearchInput,
    ProductSearchResult,
)
from app.services.normalization import normalize

# Explicit attributes are hard filters, never mere score bonuses.
FEATURES = {
    "qr",
    "1d",
    "2d",
    "4g",
    "usb-c",
    "ethernet",
    "kablosuz",
    "kablolu",
    "bluetooth",
    "wifi",
    "offline",
    "rugged",
}
STOPWORDS = {
    "bir",
    "olan",
    "stokta",
    "stoklu",
    "uygun",
    "ekle",
    "ekler",
    "misin",
    "ve",
    "icin",
    "model",
    "modeli",
    "tipi",
    "tl",
    "altinda",
    "ustune",
    "cikmadan",
    "tane",
    "adet",
    "daha",
    "goster",
}


def tokens(value):
    return set(normalize(value).split())


async def search_products(connection, args: ProductSearchInput) -> ProductSearchResult:
    query = normalize(args.query)
    words = tokens(query)
    required = set(map(normalize, args.filters.required_tags)) | (words & FEATURES)
    filters = args.filters.model_copy(update={"required_tags": sorted(required)})
    statement = sa.select(products).where(products.c.active.is_(True))
    rows = (await connection.execute(statement)).mappings().all()
    # Identify explicit ID/SKU without prefix-matching the base to its Plus sibling.
    identifiers = {word for word in words if word.startswith(("prd-", "tbr-"))}
    model_rows = [
        row
        for row in rows
        if len(tokens(row["name_tr"])) >= 2 and set(normalize(row["name_tr"]).split()[:2]) <= words
    ]
    model_ids = {row["product_id"] for row in model_rows}
    plus_requested = "plus" in words or any(word.endswith("-plus") for word in identifiers)
    ranked = []
    for row in rows:
        if filters.category and row["category"] != filters.category:
            continue
        if filters.max_price_try is not None and row["price_try"] > filters.max_price_try:
            continue
        if identifiers and not (
            {normalize(row["product_id"]), normalize(row["sku"])} & identifiers
        ):
            continue
        if not identifiers and model_ids and row["product_id"] not in model_ids:
            continue
        is_plus = "plus" in tokens(" ".join(row["tags"])) or row["sku"].upper().endswith("PLUS")
        if is_plus != plus_requested:
            continue
        tags = set(map(normalize, row["tags"]))
        if not required <= tags:
            continue
        aliases = [normalize(value) for value in row["aliases"].get(args.locale, [])]
        name = normalize(row["name_tr"])
        available_words = tokens(name + " " + " ".join(aliases) + " " + " ".join(tags))
        relevant = {word for word in words - STOPWORDS if not re.fullmatch(r"\d+", word)}
        matched = relevant & available_words
        # A query must match words, an identifier, or have explicit structural constraints.
        if relevant and not matched and not identifiers:
            continue
        if not query and not (filters.category or required or filters.max_price_try is not None):
            # Empty query is a bounded catalog browse, ordered by price then ID.
            matched = set()
        score = (100 if identifiers else 0) + (50 if row["product_id"] in model_ids else 0)
        score += 20 if query in aliases or query == name else 0
        score += len(matched)
        evidence = sorted(matched) + [f"tag:{tag}" for tag in sorted(required)]
        if identifiers:
            evidence.append("explicit_id_or_sku")
        if filters.max_price_try is not None:
            evidence.append(f"max_price_try<={filters.max_price_try}")
        if not evidence:
            evidence.append("active_catalog")
        result = ProductMatch(
            **{key: row[key] for key in ProductMatch.model_fields if key != "match_evidence"},
            match_evidence=evidence,
        )
        ranked.append((score, row["price_try"], row["product_id"], result))
    ranked.sort(key=lambda row: (-row[0], row[1], row[2]))
    # Even in_stock_only=false never promotes unavailable items to recommendations.
    return ProductSearchResult(
        recommendations=[row[3] for row in ranked if row[3].stock_qty > 0][: args.limit],
        unavailable_matches=[row[3] for row in ranked if row[3].stock_qty == 0][: args.limit],
        applied_filters=filters,
    )


async def get_knowledge_entries(
    connection, args: KnowledgeInput, *, today: date | None = None
) -> KnowledgeResult:
    statement = sa.select(knowledge_entries).where(
        knowledge_entries.c.active.is_(True),
        knowledge_entries.c.locale == args.locale,
        knowledge_entries.c.effective_from
        <= (today or datetime.now(ZoneInfo("Europe/Istanbul")).date()),
    )
    if args.topic:
        statement = statement.where(knowledge_entries.c.topic == args.topic)
    rows = (await connection.execute(statement)).mappings().all()
    words = tokens(args.query) - STOPWORDS
    ranked = []
    for row in rows:
        title_score = len(words & tokens(row["title"])) * 3
        body_score = len(words & tokens(row["body"] + " " + " ".join(row["applies_to"])))
        if args.topic or not words or title_score + body_score:
            ranked.append((title_score + body_score, row))
    ranked.sort(key=lambda entry: (-entry[0], entry[1]["knowledge_id"]))
    # Keep all effective supplemental records of the selected topic together.
    selected_topics = {row["topic"] for _, row in ranked[:1]} if not args.topic else {args.topic}
    selected = [row for row in rows if row["topic"] in selected_topics]
    selected.sort(key=lambda row: row["knowledge_id"])
    return KnowledgeResult(
        entries=[
            KnowledgeEntry(**{key: row[key] for key in KnowledgeEntry.model_fields})
            for row in selected[: args.limit]
        ]
    )
