"""Search shadows only: preserve original user/catalog text for display and evidence."""

import re
import unicodedata
from decimal import Decimal

PRICE_CEILING_MARKERS = (
    "altinda",
    "ustune cikmadan",
    "en fazla",
    "butce",
    "limit",
    "tavan",
    "kadar",
    "asmayan",
    "gecmeyen",
)


def has_price_intent(value: str) -> bool:
    normalized = normalize(value)
    return bool(re.search(r"\b(?:tl|try|lira\w*)\b|₺", value, re.IGNORECASE)) or any(
        marker in normalized for marker in PRICE_CEILING_MARKERS
    )


def normalize(value: str) -> str:
    value = value.translate(str.maketrans({"İ": "i", "I": "i", "ı": "i"})).lower()
    value = "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
    value = " ".join(re.sub(r"[^a-z0-9-]+", " ", value).split())
    for pattern, replacement in (
        (r"\bwi[ -]?fi\b", "wifi"),
        (r"\busb[ -]c\b", "usb-c"),
        (r"\bcevrim[ -]?disi\b", "offline"),
    ):
        value = re.sub(pattern, replacement, value)
    return value


def parse_money(value: str) -> Decimal:
    value = re.sub(r"\s*TL\s*$", "", value.strip(), flags=re.IGNORECASE)
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?", value):
        raise ValueError("Belirsiz veya geçersiz Türkçe para biçimi.")
    return Decimal(value.replace(".", "").replace(",", "."))


def numeric_slots(value: str) -> dict:
    lowered = value.lower()
    amounts = re.findall(r"(?<![\w.,])([0-9][0-9.,]*)\s*tl\b", lowered)
    raw_quantities = re.findall(
        r"(?<![\w.,])([-+]?\d[\d.,]*)\s*(?:adet|adede|tane|lokasyon|şube|lisans)\b", lowered
    )
    if any(not re.fullmatch(r"\d+", value) for value in raw_quantities):
        raise ValueError("Miktar negatif veya kesirli olamaz.")
    quantities = raw_quantities
    if not quantities and "cikar" in normalize(value):
        quantities = re.findall(r"(?<![\w.,-])(\d+)['’]?[ea]\b", lowered)
    if len(set(amounts)) > 1 or len(set(quantities)) > 1:
        raise ValueError("Birden çok sayısal hedef; ayrı planlama gerekir.")
    ceiling = any(marker in normalize(value) for marker in PRICE_CEILING_MARKERS)
    return {
        "quantity": int(quantities[0]) if quantities else None,
        "max_price_try": parse_money(amounts[0]) if amounts and ceiling else None,
    }
