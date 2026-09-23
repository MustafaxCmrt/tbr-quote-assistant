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
    currency = bool(re.search(r"\b(?:tl|try|lira\w*)\b|₺", value, re.IGNORECASE))
    # Temporal "until now/today" and superlative "en ucuz" (cheapest) are not ceilings.
    text = re.sub(r"\b(?:(?:simdiye|bugune) kadar|en ucuz)\b", "", normalize(value))
    # A magnitude word can end a numeric or written amount (8 bin / on bin).
    # Recognize that monetary fragment without pretending to parse its value.
    amount_tail = r"(?<![\w.,-])(?:\d[\d.,]*|bin)"
    for marker in PRICE_CEILING_MARKERS:
        suffix = r"\w*" if marker in {"butce", "limit", "tavan"} else ""
        if re.search(r"\b" + re.escape(marker) + suffix + r"\b", text) and (
            # Conservative safety net: currency + a ceiling marker needs no parsed number.
            currency
            or marker not in {"kadar", "ucuz"}
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
            amount_tail + r"\s*(?:(?:tl|try|lira\w*)\b|₺)|₺\s*\d",
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


COMMAND_VERB = r"\b(?:ekle(?:r|yin)?|degistir(?:ir|in)?|guncelle|cikar|kaldir|sil)\b"
QUOTED_SPANS = r'"([^"]*)"|“([^”]*)”|«([^»]*)»|„([^“”]*)[“”]|‘([^’]*)’'


def has_unauthorized_command(value: str) -> bool:
    """A quoted, hypothetical or approval-gated command is talked about, not given."""
    for span in re.finditer(QUOTED_SPANS, value):
        if re.search(COMMAND_VERB, normalize(" ".join(g for g in span.groups() if g))):
            return True
    text = normalize(value)
    return bool(
        # Conditional verb forms: eklersem, eklesek, degistirirsen, silinirse...
        re.search(
            r"\b(?:ekle|degistir|guncelle|cikar|kaldir|sil)(?:i?n)?(?:ir|er|ar|r)?s[ae]"
            r"(?:m|k|n|niz|ydi\w*)?\b",
            text,
        )
        # Reported or supposed speech: "ekle dersem", "diyelim ki ekle".
        or re.search(
            r"\b(?:der(?:se|sem|sek|sen|seniz)|de(?:sem|sek|sen|seniz)|denirse|dedigimde|"
            r"diyelim|varsayalim|farz\s+edelim)\b|\bne\s+(?:demek|anlam\w*)\b",
            text,
        )
        # The user reserved approval for later.
        or re.search(
            r"\bonay\w*\s+(?:(?:iste|bekle|sor)\w*|al(?:in|iniz|madan)?\b)"
            # "sormadan ekle" (add without asking) is itself the instruction.
            r"|\b(?:bana|benden)\s+(?:once\s+)?(?:sor(?!madan|maksizin)|onay)\w*"
            r"|\bonce\s+(?:bana\s+)?sor(?!madan|maksizin)\w*",
            text,
        )
    )


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


# Typographic minus/dash/plus signs must not vanish in front of a quantity.
SIGNS = str.maketrans(dict.fromkeys("‐‑‒–—−﹣－", "-") | {
    "﹢": "+",
    "＋": "+",
})
QUANTITY_UNIT = r"(?:adet|adede|tane|lokasyon|şube|lisans)\b"
NUMBER_WORDS = {
    "iki", "uc", "dort", "bes", "alti", "yedi", "sekiz", "dokuz", "on", "yirmi", "otuz",
    "kirk", "elli", "altmis", "yetmis", "seksen", "doksan", "yuz", "bin", "birkac", "bircok",
    "kac", "birer", "ikiser", "yarim", "cift", "duzine",
}  # fmt: skip


def has_unresolved_quantity(value: str) -> bool:
    """A quantity was stated, but not as a plain integer: never default it to one."""
    for match in re.finditer(r"(\S+)\s+" + QUANTITY_UNIT, value.translate(SIGNS).lower()):
        word = normalize(match[1])
        if re.fullmatch(r"\d+|bir|tek", word):
            continue
        if re.search(r"\d", word) or word in NUMBER_WORDS:
            return True
    return False


TL_AMOUNT = r"(?<![\w.,])([0-9][0-9.,]*)\s*tl\b"
MONEY_WORDS = (
    "bir|iki|uc|dort|bes|alti|yedi|sekiz|dokuz|on|yirmi|otuz|kirk|elli|altmis|yetmis|seksen"
    "|doksan|yuz|bin|milyon|bucuk"
)
# Units after a bare number that make it a quantity, time or size, not money.
NON_MONEY_UNIT = r"(?:adet|adede|tane|lokasyon|şube|lisans|gün|gun|hafta|ay|saat|yıl|yil|dakika|mm)"


def has_unparsed_money(value: str) -> bool:
    """One parsed TL amount does not mean every money condition was understood.

    Checks amounts left after removing parsed TL amounts; a bare currency note
    ("para birimi TRY", "kaç TL") is not a second limit.
    """
    rest = re.sub(TL_AMOUNT, " ", value.translate(SIGNS).lower())
    if re.search(r"₺\s*\d|\d\s*₺", rest):
        return True
    if re.search(r"\b(?:\d+|" + MONEY_WORDS + r")\s+(?:tl|try|lira\w*)\b", normalize(rest)):
        return True
    # A thousand-scale bare number (bütçem 5.000) is a limit the parser cannot bind.
    return bool(
        re.search(
            r"(?<![\w.,-])(?:\d{1,3}(?:\.\d{3})+|\d{4,})(?:,\d{1,2})?(?![\w.,-])"
            r"(?!\s*['’]?\s*" + NON_MONEY_UNIT + r")",
            rest,
        )
    )


# "Birim fiyat/bütçe/tutar", "adet başı", "tanesi" bind a limit to one unit.
UNIT_SCOPE = r"\b(?:birim\w*|tanesi\w*|her\s+biri\w*|(?:adet|tane)\s+bas\w*|basina)\b"
TOTAL_SCOPE = (
    r"\btoplam\w*\b(?!\s+\d+\s+(?:adet|adede|tane|lokasyon|sube|lisans)\b)"
    r"|\b(?:hepsi\w*|tamami\w*|tumu\w*|butun\w*|birlikte|ikisi\w*)\b"
    r"|\bsepet\w*\s+(?:tutar\w*|toplam\w*|deger\w*|\d)"
    r"|\bteklif\w*\s+(?:tutar\w*|toplam\w*|deger\w*|butce\w*)|\btutar\w*"
)
BUDGET_SCOPE = r"\b(?:butce\w*|harca\w*|par(?:am|amiz)\b)"


def price_limit_scope(value: str) -> str | None:
    """Classify what a money limit applies to: 'total', 'unit', 'budget' (ambiguous) or None.

    max_price_try is only a unit list-price ceiling (B04), so a total or ambiguous
    budget must be clarified instead of being narrowed to a unit limit.
    """
    text = normalize(value)
    if re.search(TOTAL_SCOPE, re.sub(r"\bbirim\s+\w+", " ", text)):
        return "total"
    if re.search(UNIT_SCOPE, text):
        return "unit"
    if re.search(BUDGET_SCOPE, text):
        return "budget"
    return None


def numeric_slots(value: str) -> dict:
    lowered = value.translate(SIGNS).lower()
    amounts = re.findall(TL_AMOUNT, lowered)
    raw_quantities = re.findall(r"(?<![\w.,+-])([-+]?\d[\d.,]*)\s*" + QUANTITY_UNIT, lowered)
    if any(not re.fullmatch(r"\d+", value) for value in raw_quantities):
        raise ValueError("Miktar negatif veya kesirli olamaz.")
    quantities = raw_quantities
    if not quantities and "cikar" in normalize(value):
        quantities = re.findall(r"(?<![\w.,-])(\d+)['’]?[ea]\b", lowered)
    # 8.500 TL and 8500 TL are one limit; compare values, not spellings.
    if len({parse_money(a) for a in amounts}) > 1 or len(set(quantities)) > 1:
        raise ValueError("Birden çok sayısal hedef; ayrı planlama gerekir.")
    ceiling = any(marker in normalize(value) for marker in PRICE_CEILING_MARKERS)
    return {
        "quantity": int(quantities[0]) if quantities else None,
        "max_price_try": parse_money(amounts[0]) if amounts and ceiling else None,
    }
