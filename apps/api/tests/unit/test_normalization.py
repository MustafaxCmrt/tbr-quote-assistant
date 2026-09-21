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
