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
        # Written amounts with a currency (beş yüz TL) and any number bound to a
        # limit word (azami 500, üst sınır bin, 500 ödeyebilirim) are money
        # conditions too, in reads as well as writes.
        or re.search(rf"\b(?:{MONEY_WORDS}) (?:tl|try|lira\w*)\b", text)
        or has_limit_bound_number(text)
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
QUOTED_SPANS = (
    r'"([^"]*)"|“([^”]*)”|«([^»]*)»|„([^“”]*)[“”]|‘([^’]*)’|`([^`]*)`'
    # A straight single quote opens after a boundary and closes before one, so
    # Turkish suffix apostrophes (Air'i, TL'ye) are never taken for quotes; one
    # inside the quote stays inside ('BlueScan Air'i ekle' ifadesi).
    r"|(?<![^\s(\[:;,])'((?:[^']|'(?=\w))+)'(?![^\s.,;:!?)\]])"
)
# An opening quote left after balanced spans are removed never closes. A straight
# single quote followed later by another one was closed by a suffix ('Air'ı ekle).
UNCLOSED_QUOTE = r"[\"“«„‘`]|(?<![^\s(\[:;,])'(?=[^\s'])(?![^']*')"
# Granted approval; any other mention of approval (önce onayımı al, onay
# vermedim, onay almadan) reserves the decision for later.
GRANTED_APPROVAL = (
    r"\b(?:benden\s+|bizden\s+|musteriden\s+)?onay\w*\s+"
    r"(?:alindi|verildi|var|verdim|verdik|veriyorum|veriyoruz|aldim|aldik)\b"
    r"|\bonay(?:ladim|ladik|landi|liyorum|liyoruz)\b"
)


def has_command(text: str) -> bool:
    """A quote-changing instruction in normalized text: a verb or 'toplam N olsun'."""
    return bool(re.search(COMMAND_VERB, text) or re.search(r"\btoplam\w*\b.*\bolsun\b", text))


def strip_quoted_commands(value: str) -> tuple[str, bool]:
    """Blank quoted spans that contain a command; quoted product names stay.

    An unclosed quote quotes the rest of the message.
    """
    found = False

    def blank(match):
        nonlocal found
        inner = " ".join(g for g in match.groups() if g)
        if has_command(normalize(inner)):
            found = True
            return " "
        # Keep the words, drop the marks: only unbalanced marks may remain.
        return f" {inner} "

    stripped = re.sub(QUOTED_SPANS, blank, value)
    opening = re.search(UNCLOSED_QUOTE, stripped)
    if opening and has_command(normalize(stripped[opening.end() :])):
        found = True
        stripped = stripped[: opening.start()] + " "
    return stripped, found


def has_unauthorized_command(value: str) -> bool:
    """A quoted, hypothetical or approval-gated command is talked about, not given.

    A quoted command only blocks the message when no command remains outside
    the quotes; the planner then acts on the unquoted instruction alone.
    """
    outside, quoted = strip_quoted_commands(value)
    text = normalize(outside)
    if quoted and not has_command(text):
        return True
    return bool(
        # Conditional verb forms: eklersem, eklesek, degistirirsen, silinirse...
        re.search(
            r"\b(?:ekle|degistir|guncelle|cikar|kaldir|sil)(?:i?n)?(?:ir|er|ar|r)?s[ae]"
            r"(?:m|k|n|niz|ydi\w*)?\b",
            text,
        )
        # Reported or supposed speech: "ekle dersem", "... yazarsam", "diyelim ki".
        or re.search(
            r"\b(?:(?:de|der|yaz|yazar|soyle|soyler)s[ae](?:m|k|n|niz)?|denirse|yazilirsa|"
            r"dedigimde|yazdigimda|soyledigimde|diyelim|varsayalim|farz\s+edelim)\b"
            r"|\bne\s+(?:demek|anlam\w*)\b",
            text,
        )
        # Approval next to any form of an action verb (ekle, ekleme): only a
        # granted one lets it run. "Bekleme onayını nasıl veririm?" is a question.
        or (
            re.search(r"\b(?:ekle|degistir|guncelle|cikar|kaldir|sil|toplam)\w*", text)
            and re.search(r"\bonay\w*", re.sub(GRANTED_APPROVAL, " ", text))
        )
        # "sormadan ekle" (add without asking) is itself the instruction.
        or re.search(
            r"\b(?:bana|benden)\s+(?:once\s+)?(?:sor|danis)(?!madan|maksizin)\w*"
            r"|\bonce\s+(?:bana\s+|benden\s+)?(?:sor|danis)(?!madan|maksizin)\w*",
            text,
        )
        # First-person questions (ekleyelim mi, eklesem mi); "ekler misin" is a request.
        or re.search(
            r"\b(?:(?:ekle|degistir|guncelle|kaldir)\w*"
            r"|(?:sil|cikar)[ae]?(?:yim|lim|sem|sek|sam|sak|meli\w*|mali\w*))"
            r"\s+m[iu](?:yim|yiz|dir)?\b",
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
    "kac", "birer", "ikiser", "yarim", "cift", "duzine", "bucuk", "ceyrek",
}  # fmt: skip
DISTRIBUTIVE = r"\b(?:birer|ikiser|ucer|dorder|beser|altiser|yediser|sekizer|dokuzar|onar|yirmiser)\b"


def has_unresolved_quantity(value: str) -> bool:
    """A quantity was stated, but not as a plain integer: never default it to one."""
    lowered = value.translate(SIGNS).lower()
    # Unit-first (adet: 2) and distributive (2'şer, ikişer) forms are not parsed.
    if re.search(r"\b(?:adet|tane|miktar\w*|say[ıi]\w*)\s*[:=]", lowered):
        return True
    if re.search(r"\d\s*['’]\s*ş?[ea]r\b", lowered) or re.search(DISTRIBUTIVE, normalize(value)):
        return True
    for match in re.finditer(r"(\S+)\s+" + QUANTITY_UNIT, lowered):
        word = normalize(match[1])
        if re.fullmatch(r"\d+|bir|tek", word):
            continue
        if re.search(r"\d", word) or word in NUMBER_WORDS:
            return True
    return False


# Words after a number that bind it: a unit, money, a Turkish case suffix (3'e),
# order, or a date/campaign context (2026 kampanyası).
BOUND_NUMBER = (
    r"adet\w*|adede|tane\w*|lokasyon\w*|sube\w*|lisans\w*|mm|cm|gb|dpi|ay\w*|gun\w*|yil\w*"
    r"|saat\w*|hafta\w*|dakika\w*|kampanya\w*|sezon\w*|donem\w*|tarih\w*|tl|try|lira\w*"
    r"|y?[ea]|[dt][ea]n?|inci|nci|uncu|ncu"
)


def number_context(value: str) -> str:
    """Rewrite percentages and dates so a bare-number check can tell them apart."""
    value = re.sub(r"(?<![\w.,])\d{1,2}[./]\d{1,2}[./]\d{2,4}(?![\w.,]\d)", " tarih ", value)
    return re.sub(r"%\s*(?=\d)", " yüzde ", value)


def has_unbound_number(text: str) -> bool:
    """A bare number (2, 2x, x2) tied to no unit, money or suffix is an unread quantity.

    Takes normalized number_context() text with product names/IDs removed (model
    numbers: BluePrint 80). Percentages and identifiers (model numarası 80) are not.
    """
    text = re.sub(r"\b(?:\d+ )*\d+ (?:tl|try|lira\w*)\b", " ", text)
    text = re.sub(r"\b(?:yuzde|model|numara\w*|kod\w*|seri\w*|no) \d+\b", " ", text)
    return bool(
        re.search(r"(?<![\w-])(?:x?\d+x?)(?![\w-])(?!\s+(?:" + BOUND_NUMBER + r")\b)", text)
    )


# A size in the text is a catalog tag (58mm, 203dpi): a stated size is a requirement.
def size_tags(text: str) -> set[str]:
    return {f"{n}{unit}" for n, unit in re.findall(r"\b(\d+) ?(mm|dpi)\b", normalize(text))}


TL_AMOUNT = r"(?<![\w.,])([0-9][0-9.,]*)\s*tl\b"
MONEY_WORDS = (
    "bir|iki|uc|dort|bes|alti|yedi|sekiz|dokuz|on|yirmi|otuz|kirk|elli|altmis|yetmis|seksen"
    "|doksan|yuz|bin|milyon|bucuk"
)
# Units after a bare number that make it a quantity, time, size or date, not money.
NON_MONEY_UNIT = (
    r"(?:adet|adede|tane|lokasyon|şube|lisans|gün|gun|hafta|ay|saat|yıl|yil|dakika|mm"
    r"|kampanya|sezon|dönem|donem|tarih)"
)
# A limit word next to a number binds it as money even without a currency:
# "limitim 500", "bütçem beş yüz", "en fazla 5.000", "500'ün altında".
LIMIT_BEFORE = (
    r"(?:limit\w*|butce\w*|tavan\w*|sinir\w*|masraf\w*|harca\w*|maksimum\w*|max|azami"
    r"|en (?:fazla|cok))"
)
LIMIT_AFTER = (
    r"(?:altinda\w*|alti|asma\w*|asmayan|gecme\w*|ustune\w*|kadar|limit\w*|butce\w*|tavan\w*"
    r"|ode\w*|harca\w*|ayir\w*)"
)
SPOKEN_NUMBER = rf"(?:\d+(?: \d{{3}})*|(?:{MONEY_WORDS})(?: (?:{MONEY_WORDS}))*)"
# Case ending split off a number by an apostrophe: 500'ün altında, 500'e kadar.
CASE_ENDING = r"(?:u|un|in|nin|e|a|ye|ya|i|yi|den|dan|ten|tan)"
NON_MONEY_UNIT_NORMALIZED = (
    r"(?:adet|adede|tane|lokasyon|sube|lisans|gun|hafta|ay|saat|yil|dakika|mm|x)\w*"
)


def has_limit_bound_number(text: str) -> bool:
    """A number tied to a limit word in normalized text (currency-free money)."""
    for match in re.finditer(
        rf"\b(?:{LIMIT_BEFORE} (?:\w+ )?({SPOKEN_NUMBER})|({SPOKEN_NUMBER}) (?:{CASE_ENDING} )?"
        rf"{LIMIT_AFTER})\b(?! {NON_MONEY_UNIT_NORMALIZED}\b)",
        text,
    ):
        amount = match[1] or match[2]
        # The article "bir" (bir kılıf) is not an amount.
        if amount not in {"bir", "tek"}:
            return True
    return False


def has_unparsed_money(value: str) -> bool:
    """One parsed TL amount does not mean every money condition was understood.

    Checks amounts left after removing parsed TL amounts; a bare currency note
    ("para birimi TRY", "kaç TL") is not a second limit.
    """
    lowered = value.translate(SIGNS).lower()
    # Dates (23.09.2026) are not amounts; a placeholder keeps removed amounts
    # from making neighbours adjacent (BluePrint 80 [5.000 TL] altında).
    lowered = re.sub(r"(?<![\w.,])\d{1,2}[./]\d{1,2}[./]\d{2,4}(?![\w.,]\d)", " tarih ", lowered)
    rest = re.sub(TL_AMOUNT, " amountx ", lowered)
    # Identifier numbers (model numarası 2026, kod 80) are not amounts either.
    rest = re.sub(r"\b(?:model|numara\w*|kod\w*|seri\w*|no)\s*[:.]?\s*\d+", " ref ", rest)
    if re.search(r"₺\s*\d|\d\s*₺", rest):
        return True
    if re.search(r"\b(?:\d+|" + MONEY_WORDS + r")\s+(?:tl|try|lira\w*)\b", normalize(rest)):
        return True
    if has_limit_bound_number(normalize(rest)):
        return True
    # A thousand-scale bare number (bütçem 5.000, even before a full stop) is a
    # limit the parser cannot bind.
    return bool(
        re.search(
            r"(?<![\w.,-])(?:\d{1,3}(?:\.\d{3})+|\d{4,})(?:,\d{1,2})?(?![\w-]|[.,]\d)"
            r"(?!\s*['’]?\s*" + NON_MONEY_UNIT + r")",
            rest,
        )
    )


# "Birim fiyat/bütçe/tutar", "adet başı", "tanesi" bind a limit to one unit.
UNIT_SCOPE = r"\b(?:birim\w*|tanesi\w*|her\s+biri\w*|(?:adet|tane)\s+bas\w*|basina)\b"
TOTAL_SCOPE = (
    r"\btoplam\w*\b(?!\s+\d+\s+(?:adet|adede|tane|lokasyon|sube|lisans)\b)"
    r"|\b(?:hepsi\w*|tamami\w*|tumu\w*|butun\w*|birlikte|ikisi\w*)\b"
    # "Sepet tutarı / sepetin toplamı", but not the dative "sepete ... ekle".
    r"|\bsepet(?:in|im|imin|imiz|imizin|teki)?\s+(?:tutar\w*|toplam\w*|deger\w*|\d)"
    r"|\bteklif\w*\s+(?:tutar\w*|toplam\w*|deger\w*|butce\w*)|\btutar\w*"
)
# Spending words that may mean the whole purchase: bütçe, harcama, masraf, ödeyeceğim, ayırdım.
BUDGET_SCOPE = (
    r"\b(?:butce\w*|harca\w*|maliyet\w*|masraf\w*|gider\w*|fatura\w*|ode(?:me|ye|n)\w*"
    r"|ayir\w*|par(?:am|amiz)\b)"
)


def price_limit_scope(value: str) -> str | None:
    """Classify what a money limit applies to: 'total', 'unit', 'budget' (ambiguous) or None.

    max_price_try is only a unit list-price ceiling (B04), so a total or ambiguous
    budget must be clarified instead of being narrowed to a unit limit. Any
    unqualified total or budget wins over unit wording elsewhere in the message:
    "birim fiyatı 9.000 TL altında; bütçem 9.000 TL" still has an open budget.
    """
    text = normalize(value)
    # "Birim bütçem", "birim tutarı", "(birim) fiyat(ının) tutarı" name one unit's price.
    unqualified = re.sub(
        r"\bbirim\s+fiyat\w*\s+tutar\w*|\bbirim\s+\w+|\bfiyat\w*\s+tutar\w*", " ", text
    )
    if re.search(TOTAL_SCOPE, unqualified):
        return "total"
    if re.search(BUDGET_SCOPE, unqualified):
        return "budget"
    if re.search(UNIT_SCOPE, text):
        return "unit"
    return None


def numeric_slots(value: str) -> dict:
    # A detached sign ("- 2 adet") still signs the quantity.
    lowered = re.sub(r"(?<![\w.,])([-+])\s+(?=\d)", r"\1", value.translate(SIGNS).lower())
    if re.search(r"\d\s*[/\\]\s*\d+\s*" + QUANTITY_UNIT, lowered):
        raise ValueError("Kesirli miktar desteklenmez.")
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
