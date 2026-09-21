from decimal import Decimal

import pytest

from app.services.normalization import normalize, numeric_slots, parse_money


def test_turkish_letters_and_feature_tokens():
    assert normalize("İ I ı i Şarj USB-C QR 2D 4G Plus") == "i i i i sarj usb-c qr 2d 4g plus"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("9.000", "9000"),
        ("9000", "9000"),
        ("8.500 TL", "8500"),
        ("1.500 TL", "1500"),
        ("1.500,50", "1500.50"),
        ("1500,50", "1500.50"),
    ],
)
def test_money_formats(text, expected):
    assert parse_money(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["1.50", "9,000", "-50", "NaN", "1.2.3", "1e3"])
def test_ambiguous_money_rejected(text):
    with pytest.raises(ValueError):
        parse_money(text)


def test_price_is_not_quantity():
    assert numeric_slots("2 adet, 9.000 TL altında") == {
        "quantity": 2,
        "max_price_try": Decimal(9000),
    }
    assert numeric_slots("8.500 TL üstüne çıkmadan") == {
        "quantity": None,
        "max_price_try": Decimal(8500),
    }


@pytest.mark.parametrize("value", ["-2 adet", "1,5 adet", "1.5 tane", "+3 adet"])
def test_signed_or_fractional_quantities_rejected(value):
    with pytest.raises(ValueError):
        numeric_slots(value)


def test_apostrophe_target_quantity():
    assert numeric_slots("Miktarı 3'e çıkar.")["quantity"] == 3


@pytest.mark.parametrize(
    "marker",
    [
        "altında",
        "üstüne çıkmadan",
        "en fazla",
        "bütçe",
        "limit",
        "tavan",
        "kadar",
        "aşmayan",
        "geçmeyen",
    ],
)
def test_every_supported_ceiling_marker_has_matching_intent_detection(marker):
    from app.services.normalization import has_price_intent

    assert has_price_intent(f"5.000 {marker}") is True
    assert numeric_slots(f"5.000 TL {marker}")["max_price_try"] == Decimal(5000)


@pytest.mark.parametrize("currency", ["TL", "₺", "lira", "liraya", "TRY"])
def test_currency_without_supported_amount_requests_clarification(currency):
    from app.services.normalization import has_price_intent

    assert has_price_intent(f"beş bin {currency}") is True
    assert numeric_slots(f"beş bin {currency}")["max_price_try"] is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("şimdiye kadar ekle", False),
        ("Şimdiye kadar eklediğime 1 tane daha ekle", False),
        ("bugüne kadar 2 adet ekle", False),
        ("5.000 TL'ye kadar", True),
        ("5.000 kadar", True),
        ("Şimdiye kadar eklemedim; 5.000 liraya kadar okuyucu ekle", True),
        ("Bütçe sınırlı, ucuz okuyucu ekle", True),
    ],
)
def test_kadar_price_intent_distinguishes_time_and_amount(text, expected):
    from app.services.normalization import has_price_intent

    assert has_price_intent(text) is expected


def test_kadar_currency_ceiling_is_parsed():
    assert numeric_slots("5.000 TL'ye kadar ekle")["max_price_try"] == Decimal(5000)
