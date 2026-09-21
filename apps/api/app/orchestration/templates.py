"""Responses use actual committed tool results; retrieved bodies remain labelled data."""

from app.services.evidence import EvidenceBundle, Source


def render(logs, notice, mode):
    sources = {}
    claims = []
    lines = [notice] if notice else []
    recommendations = []
    for log in logs:
        for source in log["sources"]:
            sources[(source["kind"], source["source_id"])] = Source.model_validate(source)
        output = log["output"]
        name = log["tool_name"]
        if name == "get_knowledge_entries":
            for entry in output["entries"]:
                claims.append(("knowledge", entry["knowledge_id"]))
                lines.append(
                    f"Kaynak kaydı [{entry['knowledge_id']}] — {entry['title']}:\n{entry['body']}"
                )
                if entry["topic"] == "service_policy":
                    lines.append(
                        "Şehir ve ekip müsaitliği doğrulanmadan kesin kurulum tarihi vaat edemem."
                    )
                elif entry["topic"] == "delivery_policy":
                    lines.append("Sevk aralığı kesin teslim tarihi değildir.")
        elif name == "search_products":
            for product in output["recommendations"][:3]:
                claims.append(("product", product["product_id"]))
                recommendations.append(product["product_id"])
                lines.append(
                    f"Stoklu aday: {product['name_tr']} [{product['product_id']}], birim {product['price_try']} TL, stok {product['stock_qty']}."
                )
            for product in output["unavailable_matches"][:3]:
                claims.append(("product", product["product_id"]))
                lines.append(
                    f"Stokta yok: {product['name_tr']} [{product['product_id']}]. Varsayılan öneri değildir."
                )
        elif name in {"add_to_quote", "update_quote_item", "replace_with_alternative"}:
            if output["replayed"]:
                lines.append(
                    "Bu mesajın önceki işlemi zaten kayıtlı; miktarı yeniden değiştirmedim."
                )
            else:
                lines.append("İstenen teklif işlemi kalıcı olarak kaydedildi.")
            if output.get("delta", {}).get("lost_features"):
                lost = ", ".join(output["delta"]["lost_features"])
                lines.append(
                    f"Alternatif aynı özelliklerin tümünü taşımaz. Kaybedilen özellikler: {lost}."
                )
        elif name == "get_quote":
            # Only the last quote read is rendered below, so no stale pre-mutation summary.
            pass
    quote = next((r["output"] for r in reversed(logs) if r["tool_name"] == "get_quote"), None)
    if quote:
        claims.extend(("product", item["product_id"]) for item in quote["items"])
        claims.extend(("price_rule", rule_id) for rule_id in quote["rule_ids"])
        lines.append(f"Teklif {quote['quote_id']} (sürüm {quote['version']}):")
        lines += [
            f"{p['name_tr']} [{p['product_id']}]: {p['quantity']} adet, net {p['net_total_try']} TL."
            for p in quote["items"]
        ]
        lines.append(f"Toplam: {quote['net_total_try']} TL.")
    if mode == "fallback":
        lines.insert(0, "Kaynaklara dayalı yedek moddayım; dış model çağrısı yapılmadı.")
    bundle = EvidenceBundle(sources=list(sources.values()))
    bundle.require(claims)
    return {
        "text": "\n\n".join(lines),
        "sources": bundle.model_dump(mode="json")["sources"],
        "recommended_product_ids": list(dict.fromkeys(recommendations)),
        "quote": quote,
    }
