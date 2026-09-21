"""Bounded Turkish intent/slot planning over the live catalog, never scenario fixtures."""

import re
from dataclasses import dataclass

import sqlalchemy as sa

from app.persistence.models import customers, products
from app.schemas.tools import ProductFilters, ProductSearchInput
from app.services.execution_context import Constraints, action_key
from app.services.normalization import has_price_intent, normalize, numeric_slots
from app.services.quotes import get_quote
from app.services.retrieval import FEATURES, search_products, tokens


@dataclass
class PlannedMessage:
    steps: list
    constraints: Constraints
    notice: str = ""


def category(text):
    text = normalize(text)
    for markers, name in [
        (("kilif", "sarj", "batarya", "aksesuar"), "accessory"),
        (("yazilim", "lisans", "senkron", "modul"), "software"),
        (("terminal",), "pos_terminal"),
        (("etiket",), "label_printer"),
        (("yazici",), "receipt_printer"),
        (("okuyucu", "scanner", "bluescan", "redscan", "greenscan"), "barcode_scanner"),
        (("kurulum", "hizmet"), "service"),
        (("kit", "paket"), "bundle"),
    ]:
        if any(marker in text for marker in markers):
            return name
    return None


def reference(text, quote, catalog):
    """Resolve a current item; equally plausible references require clarification."""
    text = re.sub(r"\b\w+\s+icin\b", "", normalize(text))
    # "Acil" also starts a service name; an urgency adverb is not that brand.
    text = re.sub(r"\bacil\s+olarak\b", "", text)
    words = tokens(text)
    cat = category(text)
    identifiers = {w for w in words if w.startswith(("prd-", "tbr-"))}
    required = words & FEATURES
    # A mentioned catalog brand/model cannot resolve to an unrelated lone line.
    brands = {normalize(row["name_tr"]).split()[0] for row in catalog.values()}
    named_brands = words & brands
    # A tag from another category can describe the use context, not this item.
    category_tags = {}
    for row in catalog.values():
        category_tags.setdefault(row["category"], set()).update(map(normalize, row["tags"]))
    model_ids = {
        row["product_id"]
        for row in catalog.values()
        if set(normalize(row["name_tr"]).split()[:2]) <= words
    }
    scored = []
    for item in quote.items:
        row = catalog[item.product_id]
        descriptive_words = tokens(
            row["name_tr"]
            + " "
            + " ".join(row["aliases"].get("tr", []))
            + " "
            + " ".join(row["tags"])
        )
        descriptors = words & category_tags[row["category"]]
        if not descriptors <= descriptive_words:
            continue
        if named_brands and normalize(row["name_tr"]).split()[0] not in named_brands:
            continue
        if model_ids and item.product_id not in model_ids:
            continue
        if identifiers and not identifiers & {normalize(row["product_id"]), normalize(row["sku"])}:
            continue
        if cat and row["category"] != cat:
            continue
        if not required <= set(map(normalize, row["tags"])):
            continue
        if "plus" in words and not row["sku"].endswith("PLUS"):
            continue
        names = tokens(row["name_tr"] + " " + " ".join(row["aliases"].get("tr", [])))
        score = len(words & names)
        if {normalize(row["product_id"]), normalize(row["sku"])} & words:
            score += 100
        if set(normalize(row["name_tr"]).split()[:2]) <= words:
            score += 30
        if not (score or cat or required or words & {"ayni", "aynisindan"}):
            continue
        scored.append((score, item))
    scored.sort(key=lambda pair: -pair[0])
    if not scored or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        return None
    return scored[0][1]


async def build_plan(conn, session, message_id, text, mode):
    normalized = normalize(text)
    steps = []
    topics = set()
    constraints = Constraints()
    notice = ""
    quote_id = session["quote_id"]
    quote = await get_quote(conn, quote_id)
    catalog = {
        r["product_id"]: dict(r) for r in (await conn.execute(sa.select(products))).mappings()
    }
    customer = (
        (
            await conn.execute(
                sa.select(customers).where(customers.c.customer_id == session["customer_id"])
            )
        )
        .mappings()
        .one()
    )

    def named_catalog_match(query):
        words = tokens(query)
        return any(
            len(name_words := tokens(name)) >= 2 and name_words <= words
            for row in catalog.values()
            for name in [
                " ".join(normalize(row["name_tr"]).split()[:2]),
                *row["aliases"].get("tr", []),
            ]
        )

    def unique_choice(options, query):
        if len(options) < 2:
            return options[0] if options else None

        # Price/ID ordering makes browsing stable, but is not evidence of user intent.
        def strength(candidate):
            row = catalog[candidate.product_id]
            words = tokens(query)
            exact_model = set(normalize(row["name_tr"]).split()[:2]) <= words
            exact_alias = normalize(query) in [normalize(a) for a in row["aliases"].get("tr", [])]
            return (exact_model, exact_alias, len(candidate.match_evidence))

        return options[0] if strength(options[0]) > max(map(strength, options[1:])) else None

    def call(name, **arguments):
        steps.append({"name": name, "arguments": arguments})

    def knowledge(topic):
        if topic not in topics:
            call("get_knowledge_entries", query=text, locale="tr", topic=topic, limit=10)
            topics.add(topic)

    def quote_call():
        call("get_quote", quote_id=quote_id)

    def mutation(name, product_id=None, required=(), **args):
        arguments = dict(quote_id=quote_id, **args)
        if product_id:
            arguments["product_id"] = product_id
        if name in {"add_to_quote", "replace_with_alternative"}:
            arguments["idempotency_key"] = action_key(quote_id, message_id, len(steps), name)
        if name == "add_to_quote":
            arguments["source_message_id"] = message_id
        call(name, **arguments)
        # Server-generated per-requirement tags; common ceiling and consent still apply.
        steps[-1]["required_tags"] = sorted(required)

    async def search(query, *, required=None, cat=None):
        args = ProductSearchInput(
            query=query,
            filters=ProductFilters(
                category=cat or category(query),
                max_price_try=constraints.max_price_try,
                in_stock_only=True,
                required_tags=sorted(
                    required if required is not None else tokens(query) & FEATURES
                ),
            ),
            limit=50,
        )
        call("search_products", **args.model_dump(mode="json"))
        return await search_products(conn, args)

    def finish():
        if mode == "fallback":
            knowledge("fallback")
        quote_call()
        return PlannedMessage(steps, constraints, notice)

    negated = bool(
        re.search(
            r"\b(ekleme|eklemeyin|eklemeyelim|degistirme|degistirmeyin|silme|guncelleme)\b",
            normalized,
        )
    )
    read_only = negated or "sadece" in normalized or "yalnizca" in normalized
    remove = bool(re.search(r"\b(kaldir|sil)\b", normalized))
    replace = bool(re.search(r"\bdegistir(?:ir|in)?\b", normalized))
    update = bool(re.search(r"\b(guncelle|cikar)\b", normalized))
    total = "toplam" in normalized and "olsun" in normalized
    add = bool(re.search(r"\bekle(?:r|yin)?\b", normalized))
    mutating = (remove or replace or update or total or add) and not read_only
    for markers, topic in [
        (("iade",), "return_policy"),
        (("teslim", "sevk"), "delivery_policy"),
        (("garanti",), "warranty"),
        (("rezervasyon", "gecerli"), "quote_validity"),
    ]:
        if any(word in normalized for word in markers):
            knowledge(topic)
    try:
        slots = numeric_slots(text)
    except ValueError:
        notice = "Miktar veya fiyat biçimini kesinleştiremedim. Ürün başına miktarı ve TL limitini açık yazar mısın?"
        return finish()
    # Do not silently discard a constraint that the bounded parser cannot represent.
    if mutating and has_price_intent(text) and slots["max_price_try"] is None:
        notice = "Fiyat sınırını kesinleştiremedim. Örneğin 5.000 TL altında şeklinde yazar mısın? Teklifi değiştirmedim."
        return finish()
    # Stock absence describes the source of a supported substitution, not a negated feature.
    attribute_text = re.sub(r"\bstokta olmayan\b", "", normalized)
    if mutating and re.search(
        r"\b(olmasin|olmayan|olmadan|degil\w*|istem(?:iyor|em|ez|edi|e)\w*|haric\w*|disinda)\b|\bplus[ -]?s[iu]z\b",
        attribute_text,
    ):
        notice = "Olumsuzlanan ürün veya özelliği kesinleştiremedim. İstediğin ürün kodunu belirtir misin? Teklifi değiştirmedim."
        return finish()
    # A product category somewhere in the sentence does not make a delivery,
    # price or discount noun the product itself. Those writes are unsupported.
    if (remove or replace or update) and re.search(
        r"\b(?:indirim\w*|fiyat\w*|teslim\w*|tarih\w*|garanti\w*|vade\w*)\s+(?:de\s+)?(?:kaldir|sil|degistir|guncelle)\b",
        normalized,
    ):
        notice = "Ürün miktarı veya ürün değişimi dışında bu alanı değiştiremiyorum. Hangi teklif kalemini ve işlemi istediğini belirtir misin? Teklifi değiştirmedim."
        return finish()
    if mutating and re.search(r"\bdaha\s+(ucuz|pahali)\b", normalized):
        notice = "Karşılaştırma için ürün kodunu ve fiyat sınırını belirtir misin? Teklifi değiştirmedim."
        return finish()
    plus_mentioned = "plus" in tokens(text) or any(t.endswith("-plus") for t in tokens(text))
    explicit_plus = any(
        token.startswith(("prd-", "tbr-")) and token.endswith("-plus") for token in tokens(text)
    ) or any(
        row["sku"].endswith("PLUS")
        and re.search(
            r"\b" + re.escape(" ".join(normalize(row["name_tr"]).split()[:2])) + r" plus\b",
            normalized,
        )
        for row in catalog.values()
    ) or any(
        row["sku"].endswith("PLUS")
        and any(
            "plus" in tokens(name)
            and normalize(name) != "plus model"
            and re.search(r"\b" + re.escape(normalize(name)) + r"\b", normalized)
            for name in [row["name_tr"], *row["aliases"].get("tr", [])]
        )
        for row in catalog.values()
    )
    if mutating and plus_mentioned and not explicit_plus:
        notice = "Plus seçimini kesinleştirmek için tam model adını veya ürün kodunu belirtir misin? Teklifi değiştirmedim."
        return finish()
    constraints = Constraints(
        max_price_try=slots["max_price_try"],
        explicit_plus=bool(explicit_plus),
        explicit_backorder_consent=bool(
            re.search(
                r"\b(bekleyebilirim|beklemeyi kabul ediyorum|backorder kabul ediyorum)\b",
                normalized,
            )
        ),
    )
    if constraints.max_price_try is not None:
        knowledge("price_ceiling")
    if not mutating:
        if "kurulum" in normalized:
            knowledge("service_policy")
        if "indirim" in normalized:
            knowledge("discount_policy")
        if not topics - {"price_ceiling"} and (
            category(text)
            or named_catalog_match(text)
            or any(w.startswith(("prd-", "tbr-")) for w in tokens(text))
        ):
            await search(text)
        if not topics and not category(text) and not named_catalog_match(text):
            notice = "Hangi ürün veya teklif işlemini istediğini biraz daha açık yazar mısın?"
        return finish()
    quantity = slots["quantity"]
    if replace and quantity is not None and "tamamini" not in tokens(text):
        notice = "Kısmi değişim mi, kalemin tamamının değişimi mi istediğin belirsiz. Tam değişim için kalemin tamamını ve hedef miktarı açıkça belirtir misin? Teklifi değiştirmedim."
        return finish()
    if (
        quantity is not None
        and quantity > 0
        and (
            remove or ("cikar" in tokens(text) and re.search(r"\b\d+\s+(adet|tane)\b", normalized))
        )
    ):
        notice = "Kaç adet kalmasını istediğini hedef miktarla yazar mısın? Örneğin 3 adede güncelle. Teklifi değiştirmedim."
        return finish()
    if (update or total) and quantity is None:
        notice = "Hedef miktarı belirtir misin? Teklifi değiştirmedim."
        return finish()
    if quantity is not None and quantity == 0 and not (update or remove):
        notice = "Ekleme miktarı sıfırdan büyük olmalı. Kaldırmak için açıkça kaldır yazabilirsin."
        return finish()
    # Replacement source descriptors and target requirements have different scopes.
    if replace:
        quote_call()
        if ";" in text:
            source_text, target_text = text.split(";", 1)
        else:
            split = re.search(r"\bstoklu\s+", text, re.IGNORECASE)
            source_text, target_text = (
                (text[: split.start()], text[split.end() :]) if split else (text, "")
            )
        source = reference(source_text, quote, catalog)
        if source is None:
            notice = "Değiştirilecek kalemi tek anlamlı seçemedim. Ürün kodunu belirtir misin?"
            return finish()
        row = catalog[source.product_id]
        if row["stock_qty"] == 0:
            knowledge("stock_rule")
        required = tokens(target_text) & FEATURES
        # No explicit target: retain substitution order supplied by the current catalog.
        result = await search(
            target_text
            if category(target_text)
            or required
            or any(w.startswith(("prd-", "tbr-")) for w in tokens(target_text))
            else "",
            required=required,
            cat=row["category"],
        )
        allowed = {p.product_id: p for p in result.recommendations}
        target = next(
            (allowed[pid] for pid in row["substitute_product_ids"] if pid in allowed), None
        )
        if target is None:
            notice = "Fiyat, stok ve özellik koşullarını sağlayan kayıtlı alternatif bulunamadı; teklif değişmedi."
        else:
            mutation(
                "replace_with_alternative",
                from_product_id=source.product_id,
                to_product_id=target.product_id,
                quantity=quantity,
                reason=text,
                required=required,
            )
        return finish()
    reference_intent = (
        remove
        or update
        or total
        or bool(re.search(r"\b\d+\s+(adet|tane)\s+daha\b", normalized))
        or bool(tokens(text) & {"ayni", "aynisindan"})
    )
    if reference_intent:
        quote_call()
        item = reference(text, quote, catalog)
        if item is None:
            notice = (
                "Mevcut teklifte hangi kalemi kastettiğin belirsiz. Ürün kodunu belirtir misin?"
            )
            return finish()
        if remove or update:
            mutation(
                "update_quote_item",
                item.product_id,
                quantity=0 if remove else quantity,
                reason=text,
                required=tokens(text) & FEATURES,
            )
        else:
            delta = quantity - item.quantity if total else (quantity or 1)
            if delta <= 0:
                notice = "Toplam hedef mevcut miktardan büyük değil. Azaltmak için hedef miktarla güncelle komutu ver."
                return finish()
            knowledge("quote_idempotency")
            mutation(
                "add_to_quote", item.product_id, quantity=delta, required=tokens(text) & FEATURES
            )
            if total:
                # The delta is valid only for the snapshot used to calculate it.
                # Internal metadata, never a new public tool argument.
                steps[-1]["expected_quote_version"] = quote.version
        if "indirim" in normalized or total:
            knowledge("discount_policy")
        if catalog[item.product_id]["category"] == "service":
            knowledge("service_policy")
        return finish()
    if "yoksa" in normalized:
        parts = re.split(r"\byoksa\b", text, maxsplit=1, flags=re.IGNORECASE)
        original = await search(parts[0])
        if original.recommendations:
            notice = "İlk ürün stokta; yoksa koşulu oluşmadığı için ekleme yapmadım."
            return finish()
        if not original.unavailable_matches:
            notice = "İlk ürünü doğrulayamadım; koşullu eklemeyi uygulamadım."
            return finish()
        original_choice = unique_choice(original.unavailable_matches, parts[0])
        if original_choice is None:
            notice = (
                "Koşuldaki ilk ürün belirsiz. Ürün kodunu belirtir misin? Teklifi değiştirmedim."
            )
            return finish()
        knowledge("stock_rule")
        target = await search(parts[1])
        substitute_ids = set(original_choice.substitute_product_ids)
        options = [p for p in target.recommendations if p.product_id in substitute_ids]
        selected = unique_choice(options, parts[1])
        if selected:
            mutation(
                "add_to_quote",
                selected.product_id,
                quantity=quantity or 1,
                required=tokens(parts[1]) & FEATURES,
            )
        else:
            notice = "Koşulları sağlayan tek anlamlı stoklu alternatif seçilemedi. Ürün kodunu belirtir misin?"
        return finish()
    # Each conjunction requirement gets its own search and guard tags, then one atomic group.
    content = (
        text.split(";", 1)[-1]
        if ";" in text and "ekle" not in normalize(text.split(";", 1)[0])
        else text.split(";", 1)[0]
    )
    segments = re.split(r"\bve\b", content, flags=re.IGNORECASE)
    requirements = []
    pending_features = []
    for segment in segments:
        if (
            category(segment)
            or named_catalog_match(segment)
            or any(w.startswith(("prd-", "tbr-")) for w in tokens(segment))
        ):
            requirements.append(" ".join(pending_features + [segment]))
            pending_features = []
        elif tokens(segment) & FEATURES:
            if requirements:
                requirements[-1] += " " + segment
            else:
                pending_features.append(segment)
    if pending_features:
        notice = "Özellikleri hangi ürün için istediğini belirtir misin?"
        return finish()
    if not requirements:
        notice = "Eklenecek ürünü belirleyemedim. Ürün adı veya kodunu belirtir misin?"
        return finish()
    if any("offline" in normalize(s) or "senkron" in normalize(s) for s in requirements):
        knowledge("compatibility")
    choices = []
    for segment in requirements:
        result = await search(segment)
        if result.recommendations:
            selected = unique_choice(result.recommendations, segment)
            if selected is None:
                notice = "Birden fazla ürün aynı ölçüde uyuyor. Ürün kodunu belirtir misin? Teklifi değiştirmedim."
                return finish()
            choices.append((selected, tokens(segment) & FEATURES))
        elif result.unavailable_matches:
            knowledge("stock_rule")
            if constraints.explicit_backorder_consent and customer["allow_backorder"]:
                selected = unique_choice(result.unavailable_matches, segment)
                if selected is None:
                    notice = "Birden fazla stok dışı ürün uyuyor. Ürün kodunu belirtir misin? Teklifi değiştirmedim."
                    return finish()
                choices.append((selected, tokens(segment) & FEATURES))
            else:
                notice = "İstenen ürün stokta yok. Açık bekleme onayı ve uygun müşteri olmadan eklenmez; teklif değişmedi."
                # Offer catalog alternatives as read-only evidence, never substitute silently.
                for pid in result.unavailable_matches[0].substitute_product_ids[:3]:
                    await search(
                        pid, required=tokens(segment) & FEATURES, cat=catalog[pid]["category"]
                    )
                return finish()
        else:
            notice = "İstenen koşullarda ürün bulunamadı; grup işlemi uygulanmadı."
            return finish()
    for product, required in choices:
        if any(item.product_id == product.product_id for item in quote.items):
            knowledge("quote_idempotency")
        mutation("add_to_quote", product.product_id, quantity=quantity or 1, required=required)
    if "indirim" in normalized or len(choices) > 1:
        knowledge("discount_policy")
    if any(p.category == "service" for p, _ in choices):
        knowledge("service_policy")
    return finish()
