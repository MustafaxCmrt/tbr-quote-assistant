"""Rendered claims must have actual tool evidence, not merely self-consistent sources."""

import pytest

from app.orchestration.templates import render
from app.services.errors import DomainError


@pytest.mark.parametrize(
    "name,output,kind,source_id",
    [
        (
            "get_knowledge_entries",
            {
                "entries": [
                    {
                        "knowledge_id": "K-1",
                        "title": "İade",
                        "body": "14 gün",
                        "topic": "return_policy",
                    }
                ]
            },
            "knowledge",
            "K-1",
        ),
        (
            "search_products",
            {
                "recommendations": [
                    {"product_id": "P-1", "name_tr": "Ürün", "price_try": "10.00", "stock_qty": 1}
                ],
                "unavailable_matches": [],
            },
            "product",
            "P-1",
        ),
        (
            "search_products",
            {
                "recommendations": [],
                "unavailable_matches": [{"product_id": "P-1", "name_tr": "Ürün"}],
            },
            "product",
            "P-1",
        ),
        (
            "get_quote",
            {
                "quote_id": "Q-1",
                "version": 1,
                "items": [
                    {
                        "product_id": "P-1",
                        "name_tr": "Ürün",
                        "quantity": 1,
                        "net_total_try": "10.00",
                    }
                ],
                "rule_ids": [],
                "net_total_try": "10.00",
            },
            "product",
            "P-1",
        ),
        (
            "get_quote",
            {
                "quote_id": "Q-1",
                "version": 1,
                "items": [],
                "rule_ids": ["R-1"],
                "net_total_try": "0.00",
            },
            "price_rule",
            "R-1",
        ),
    ],
)
def test_rendered_claim_requires_matching_tool_evidence(name, output, kind, source_id):
    log = {"tool_name": name, "output": output, "sources": []}
    with pytest.raises(DomainError) as missing:
        render([log], "", "fallback")
    assert missing.value.code == "SOURCE_NOT_GROUNDED"
    # An unrelated valid source is not sufficient either.
    source = {
        "kind": kind,
        "source_id": "OTHER",
        "title": "Kaynak",
        "excerpt": "Veri",
        "source": "test",
    }
    log["sources"] = [source]
    with pytest.raises(DomainError) as unrelated:
        render([log], "", "fallback")
    assert unrelated.value.code == "SOURCE_NOT_GROUNDED"
    source["source_id"] = source_id
    result = render([log], "", "fallback")
    assert result["sources"] == [source]
    assert "Kaynaklara dayalı yedek moddayım" in result["text"]
    if kind != "price_rule":
        assert source_id in result["text"]
