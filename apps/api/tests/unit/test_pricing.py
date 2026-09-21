from copy import deepcopy
from decimal import Decimal

import pytest

from app.services.errors import DomainError
from app.services.pricing import price_lines

RULES = [
    {"rule_id": key, "discount_percent": Decimal(value)}
    for key, value in [
        ("RUL-PARTNER-3", "7"),
        ("RUL-ACC-5", "5"),
        ("RUL-BUNDLE-NO-STACK", "0"),
        ("RUL-SVC-URGENT", "0"),
        ("RUL-SW-BUNDLE", "8"),
        ("RUL-PLUS-QTY", "6"),
    ]
]


def line(product="P", quantity=1, price="100", status="active"):
    return {
        "quote_item_id": product,
        "product_id": product,
        "quantity": quantity,
        "unit_price_try": Decimal(price),
        "status": status,
    }


def catalog(product="P", category="barcode_scanner", sku="TBR-P", tags=None):
    return {product: {"category": category, "sku": sku, "tags": tags or []}}


@pytest.mark.parametrize(
    ("quantity", "discount", "net"), [(2, "0.00", "15980.00"), (3, "1677.90", "22292.10")]
)
def test_partner_threshold(quantity, discount, net):
    result = price_lines(
        [line(quantity=quantity, price="7990")], catalog(), {"price_tier": "partner"}, RULES
    )["P"]
    assert result["discount_total_try"] == Decimal(discount)
    assert result["net_total_try"] == Decimal(net)


def test_plus_is_specific_even_when_partner_rate_is_larger():
    items = [line(quantity=4, price="9430")]
    original = deepcopy(items)
    result = price_lines(items, catalog(sku="TBR-P-PLUS"), {"price_tier": "partner"}, RULES)["P"]
    assert result == {
        "gross_total_try": Decimal("37720.00"),
        "discount_total_try": Decimal("2263.20"),
        "net_total_try": Decimal("35456.80"),
        "rule_ids": ["RUL-PLUS-QTY"],
    }
    assert items == original


@pytest.mark.parametrize(
    ("category", "sku", "tags", "qty", "rule", "discount"),
    [
        ("accessory", "TBR-P", [], 4, None, "0"),
        ("accessory", "TBR-P", [], 5, "RUL-ACC-5", "25"),
        ("accessory", "TBR-P-PLUS", [], 5, "RUL-PLUS-QTY", "30"),
        ("bundle", "TBR-P-PLUS", [], 5, "RUL-BUNDLE-NO-STACK", "0"),
        ("service", "TBR-P-PLUS", ["acil"], 5, "RUL-SVC-URGENT", "0"),
    ],
)
def test_specificity_and_accessory_product_threshold(category, sku, tags, qty, rule, discount):
    result = price_lines(
        [line(quantity=qty)],
        catalog(category=category, sku=sku, tags=tags),
        {"price_tier": "partner"},
        RULES,
    )["P"]
    assert result["rule_ids"] == ([rule] if rule else [])
    assert result["discount_total_try"] == Decimal(discount)


def test_software_pair_and_removed_item_restore_no_discount():
    items = [line("PRD-SW-520", price="14900"), line("PRD-SW-530", price="9900")]
    products = catalog("PRD-SW-520", "software") | catalog("PRD-SW-530", "software")
    result = price_lines(items, products, {"price_tier": "standard"}, RULES)
    assert sum(row["net_total_try"] for row in result.values()) == Decimal(22816)
    assert {tuple(row["rule_ids"]) for row in result.values()} == {("RUL-SW-BUNDLE",)}
    items[1]["status"] = "removed"
    result = price_lines(items, products, {"price_tier": "standard"}, RULES)
    assert result["PRD-SW-520"]["net_total_try"] == Decimal(14900)
    assert result["PRD-SW-520"]["rule_ids"] == []


def test_half_up_and_no_eval_unknown_rules():
    result = price_lines(
        [line(quantity=3, price="0.50")], catalog(), {"price_tier": "partner"}, RULES
    )["P"]
    assert result["discount_total_try"] == Decimal("0.11")
    assert result["net_total_try"] == Decimal("1.39")
    with pytest.raises(DomainError, match="PRICING_RULE_UNSUPPORTED"):
        price_lines(
            [],
            {},
            {"price_tier": "partner"},
            RULES
            + [{"rule_id": "EVIL", "condition": "exec(...)", "discount_percent": Decimal(100)}],
        )


def test_partner_aggregates_category_but_accessories_require_same_product():
    items = [line("A", 2), line("B", 1)]
    products = catalog("A") | catalog("B")
    result = price_lines(items, products, {"price_tier": "partner"}, RULES)
    assert result["A"]["discount_total_try"] == Decimal(14)
    assert result["B"]["discount_total_try"] == Decimal(7)
    assert sum(row["net_total_try"] for row in result.values()) == Decimal(279)
    items = [line("A", 3), line("B", 2)]
    products = catalog("A", "accessory") | catalog("B", "accessory")
    result = price_lines(items, products, {"price_tier": "partner"}, RULES)
    assert [row["rule_ids"] for row in result.values()] == [[], []]
    assert sum(row["net_total_try"] for row in result.values()) == Decimal(500)


def test_missing_required_rate_fails_closed():
    with pytest.raises(DomainError, match="PRICING_RULE_MISSING"):
        price_lines(
            [line(quantity=3)],
            catalog(),
            {"price_tier": "partner"},
            [r for r in RULES if r["rule_id"] != "RUL-PARTNER-3"],
        )
