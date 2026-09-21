"""Pure Decimal pricing; ADR-005 accepted candidate choice, not a company stacking rule.

Specificity: bundle/urgent exclusions > Plus > software bundle > accessory > partner.
Predicates are code; untrusted condition strings are never evaluated.
"""

from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

from app.services.errors import DomainError

CENT = Decimal("0.01")
KNOWN_RULES = {
    "RUL-PARTNER-3",
    "RUL-ACC-5",
    "RUL-BUNDLE-NO-STACK",
    "RUL-SVC-URGENT",
    "RUL-SW-BUNDLE",
    "RUL-PLUS-QTY",
}


def amount(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def price_lines(items, product_by_id, customer, rules):
    by_rule = {rule["rule_id"]: rule for rule in rules}
    if set(by_rule) - KNOWN_RULES:
        raise DomainError("PRICING_RULE_UNSUPPORTED", "Tanımsız fiyat kuralı yapılandırılmış.")
    active = [item for item in items if item["status"] == "active"]
    categories = Counter()
    product_quantities = Counter()
    for item in active:
        categories[product_by_id[item["product_id"]]["category"]] += item["quantity"]
        product_quantities[item["product_id"]] += item["quantity"]
    software_pair = {"PRD-SW-520", "PRD-SW-530"} <= set(product_quantities)
    results = {}
    for item in items:
        product = product_by_id[item["product_id"]]
        category = product["category"]
        rule_id = None
        if item["status"] == "active":
            if category == "bundle":
                rule_id = "RUL-BUNDLE-NO-STACK"
            elif category == "service" and "acil" in product["tags"]:
                rule_id = "RUL-SVC-URGENT"
            elif product["sku"].endswith("PLUS") and product_quantities[item["product_id"]] >= 4:
                rule_id = "RUL-PLUS-QTY"
            elif category == "software" and software_pair:
                rule_id = "RUL-SW-BUNDLE"
            elif category == "accessory" and product_quantities[item["product_id"]] >= 5:
                rule_id = "RUL-ACC-5"
            elif (
                customer["price_tier"] == "partner"
                and category in {"barcode_scanner", "receipt_printer", "label_printer"}
                and categories[category] >= 3
            ):
                rule_id = "RUL-PARTNER-3"
        if rule_id and rule_id not in by_rule:
            raise DomainError("PRICING_RULE_MISSING", "Gerekli fiyat kuralı bulunamadı.")
        percentage = by_rule[rule_id]["discount_percent"] if rule_id else Decimal(0)
        gross = amount(item["unit_price_try"] * item["quantity"])
        discount = amount(gross * percentage / Decimal(100))
        results[item["quote_item_id"]] = {
            "gross_total_try": gross,
            "discount_total_try": discount,
            "net_total_try": gross - discount,
            "rule_ids": [rule_id] if rule_id else [],
        }
    return results
