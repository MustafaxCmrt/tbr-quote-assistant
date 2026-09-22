"""Search shadows only: preserve original user/catalog text for display and evidence."""

import re
import unicodedata
from decimal import Decimal

PRICE_CEILING_MARKERS = (
    "altinda",
    "alti",
    "ucuz",
    "ustune cikmadan",
    "en fazla",
    "butce",
    "limit",
    "tavan",
    "kadar",
    "asmayan",
    "gecmeyen",
)


def has_price_ceiling_intent(value: str) -> bool:
    """Recognize a constraint even when its amount syntax is unsupported.

    Currency alone is not a ceiling: 'kaç TL?' must remain a normal read.
    Literal monetary amounts without a clear relation require clarification.
    """
    text = re.sub(r"\b(?:simdiye|bugune) kadar\b", "", normalize(value))
    # A magnitude word can end a numeric or written amount (8 bin / on bin).
    # Recognize that monetary fragment without pretending to parse its value.
    amount_tail = r"(?<![\w.,-])(?:\d[\d.,]*|bin)"
    for marker in PRICE_CEILING_MARKERS:
        suffix = r"\w*" if marker in {"butce", "limit", "tavan"} else ""
        if re.search(r"\b" + re.escape(marker) + suffix + r"\b", text) and (
            marker not in {"kadar", "ucuz"}
            # Keep amount punctuation: normalization erases decimal/apostrophe boundaries.
            # Only an adjacent amount qualifies; time/quantity units and model codes do not.
            or re.search(
                amount_tail + r"(?:\s*(?:TL|TRY|lira|₺))?"
                r"\s*['’]?(?:ye|ya|e|a|den|dan|ten|tan)?\s+" + marker + r"\b",
                value,
                re.IGNORECASE,
            )
        ):
            return True
    return bool(
        re.search(
            amount_tail + r"\s*(?:tl|try|lira\w*)\b|₺\s*\d|\d[\d.,]*\s*₺",
            value,
            re.IGNORECASE,
        )
    )


def has_backorder_consent(value: str) -> bool:
    """Accept a standalone affirmative clause, not reported/conditional consent.

    Scope question punctuation to that clause, so 'ekler misin? Bekleyebilirim.'
    stays valid. Ambiguous wording is deliberately not authorization.
    """
    phrase = r"(?:bekleyebilirim|beklemeyi kabul ediyorum|backorder kabul ediyorum)"
    text = normalize(value)
    if re.search(
        r"\b(?:demiyorum|demedim|diyemem|degil\w*|istemiyorum|istemem|"
        r"kabul etmiyorum|eger|ama|ancak|fakat|\w+(?:sa|se))\b",
        text,
    ):
        return False
    if re.search(r"""["“‘'`]\s*""" + phrase, value, re.IGNORECASE):
        return False
    # Keep each clause's terminator; only a question about consent invalidates it.
    for match in re.finditer(r"([^.!?;,\n]+)([.!?;,\n]|$)", value):
        clause = normalize(match[1])
        if match[2] != "?" and re.fullmatch(r"(?:(?:evet|tamam) )?" + phrase, clause):
            return True
    return False


def has_price_intent(value: str) -> bool:
    normalized = normalize(value)
    # Temporal "until now/today" is not a ceiling, even with an item quantity.
    price_text = re.sub(r"\b(?:simdiye|bugune) kadar\b", "", normalized)
    return bool(re.search(r"\b(?:tl|try|lira\w*)\b|₺", value, re.IGNORECASE)) or any(
        marker in price_text and (marker != "kadar" or bool(re.search(r"\d", price_text)))
        for marker in PRICE_CEILING_MARKERS
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
