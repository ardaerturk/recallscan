from api.app.models.db import CatalogItem, RecallSignal
from api.app.models.domain import MatchDecision
from api.app.services.action_memo import recommended_action
from api.app.services.utils import compact, normalize_upc, words


TIER_RANK = {
    "confirmed_match": 0,
    "supplier_review": 1,
    "watch_only": 2,
    "no_exposure": 3,
}


def match_signal_to_catalog(
    signal: RecallSignal, catalog: list[CatalogItem], *, action_source: bool = True
) -> list[MatchDecision]:
    decisions: list[MatchDecision] = []
    for item in catalog:
        decision = _decision_for_item(signal, item, action_source=action_source)
        if decision:
            decisions.append(decision)
    return sorted(decisions, key=lambda decision: (TIER_RANK[decision.tier], decision.catalog_item_id))


def _decision_for_item(signal: RecallSignal, item: CatalogItem, *, action_source: bool) -> MatchDecision | None:
    upc_match = _upc_match(signal, item)
    product_match = _product_match(signal, item)
    exclusion_match = _explicit_exclusion_match(signal, item)
    supplier_match = _supplier_chain_match(signal, item)
    ingredient_match = _ingredient_match(signal, item)
    geography_match = _geography_match(signal, item)
    category_match = _category_match(signal, item)
    lot_missing = _lot_missing(signal)

    if upc_match and action_source:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="confirmed_match",
            match_type="exact_upc",
            matched_fields={"upc": item.upc, "affected_upcs": _signal_upcs(signal)},
            missing_fields=["lot_code"] if lot_missing else [],
            explanation=f"Exact UPC match for {item.brand} {item.product_name}.",
            recommended_action=recommended_action("confirmed_match"),
        )

    if product_match and not exclusion_match and action_source:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="confirmed_match",
            match_type="brand_product",
            matched_fields={
                "brand": item.brand,
                "product_name": item.product_name,
                "source_products": _signal_product_names(signal),
            },
            missing_fields=["upc"] if not _signal_upcs(signal) else [],
            explanation="Brand and product name overlap strongly with the affected product.",
            recommended_action=recommended_action("confirmed_match"),
        )

    if (upc_match or product_match) and not exclusion_match:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="watch_only",
            match_type="product_mention",
            matched_fields={
                "brand": item.brand,
                "product_name": item.product_name,
                "source_products": _signal_product_names(signal),
                "direct_recall_notice_required": True,
            },
            missing_fields=["direct recall notice"],
            explanation="The product is mentioned, but the source is not a direct recall notice or safety alert.",
            recommended_action=recommended_action("watch_only"),
        )

    if exclusion_match:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="no_exposure",
            match_type="explicit_exclusion",
            matched_fields={"exclusion": exclusion_match, "brand": item.brand, "product_name": item.product_name},
            missing_fields=[],
            explanation="The source explicitly excludes this product family or flavor from the recall.",
            recommended_action=recommended_action("no_exposure"),
        )

    if supplier_match:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="supplier_review",
            match_type="supplier_chain",
            matched_fields={"supplier_overlap": supplier_match},
            missing_fields=["supplier lot confirmation", "facility confirmation"],
            explanation="The catalog supplier, co-manufacturer, or alias appears in the source supplier chain.",
            recommended_action=recommended_action("supplier_review"),
        )

    if ingredient_match and geography_match:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="watch_only",
            match_type="ingredient_geography",
            matched_fields={"ingredient_overlap": ingredient_match, "distribution_overlap": geography_match},
            missing_fields=["supplier evidence", "UPC", "lot code"],
            explanation="The source mentions a relevant ingredient in a geography where inventory exists, but supplier exposure is not confirmed.",
            recommended_action=recommended_action("watch_only"),
        )

    if ingredient_match or category_match:
        return MatchDecision(
            catalog_item_id=item.id,
            tier="watch_only",
            match_type="nearby_category_or_ingredient",
            matched_fields={"ingredient_overlap": ingredient_match, "category_overlap": category_match},
            missing_fields=["supplier evidence", "UPC", "lot code"],
            explanation="The signal is nearby by category or ingredient, but there is not enough evidence to pull inventory.",
            recommended_action=recommended_action("watch_only"),
        )

    return None


def _signal_upcs(signal: RecallSignal) -> list[str]:
    upcs = signal.identifiers_json.get("upcs", [])
    return [normalize_upc(str(upc)) for upc in upcs if normalize_upc(str(upc))]


def _signal_product_names(signal: RecallSignal) -> list[str]:
    names = []
    for product in signal.affected_products_json:
        value = product.get("product_name") or product.get("name") or product.get("product")
        if value:
            names.append(str(value))
    return names


def _upc_match(signal: RecallSignal, item: CatalogItem) -> bool:
    return bool(item.upc and normalize_upc(item.upc) in _signal_upcs(signal))


def _product_match(signal: RecallSignal, item: CatalogItem) -> bool:
    item_words = words(f"{item.brand} {item.product_name}")
    if len(item_words) < 2:
        return False
    for product in signal.affected_products_json:
        product_words = words(f"{product.get('brand', '')} {product.get('product_name', '')}")
        if not product_words:
            continue
        overlap = item_words & product_words
        if len(overlap) >= max(2, min(4, len(product_words))):
            return True
    return False


def _explicit_exclusion_match(signal: RecallSignal, item: CatalogItem) -> str | None:
    item_text = compact(f"{item.brand} {item.product_name} {item.category}")
    if not item_text:
        return None
    for exclusion in signal.explicit_exclusions_json:
        text = compact(exclusion.get("text") if isinstance(exclusion, dict) else str(exclusion))
        if not text:
            continue
        brand_in_scope = compact(item.brand) and compact(item.brand) in compact(signal.company or item.brand)
        if brand_in_scope and ("no other" in text or "not affected" in text):
            if any(word in item_text for word in ("sauce", "flavor", "noodle")) and any(
                word in text for word in ("sauce", "flavor", "noodle")
            ):
                return exclusion.get("text") if isinstance(exclusion, dict) else str(exclusion)
        if compact(item.product_name) in text:
            return exclusion.get("text") if isinstance(exclusion, dict) else str(exclusion)
    return None


def _supplier_chain_match(signal: RecallSignal, item: CatalogItem) -> list[str]:
    item_names = {
        compact(item.supplier_name),
        compact(item.co_manufacturer_name),
        *(compact(alias) for alias in item.supplier_aliases_json),
    }
    item_names = {name for name in item_names if name}
    chain_names = set()
    for node in signal.supplier_chain_json:
        if isinstance(node, dict):
            chain_names.add(compact(node.get("name") or node.get("supplier") or node.get("company")))
        else:
            chain_names.add(compact(str(node)))
    chain_names = {name for name in chain_names if _valid_supplier_chain_name(name)}
    matches = []
    for item_name in item_names:
        for chain_name in chain_names:
            if item_name == chain_name or item_name in chain_name or chain_name in item_name:
                matches.append(chain_name)
    return sorted(set(matches))


def _valid_supplier_chain_name(value: str) -> bool:
    if value in {"and", "or", "nor", "the", "of", "for", "from", "by", "to", "in", "on", "with", "use"}:
        return False
    if value.startswith(("of ", "for ", "from ", "by ", "to ", "in ", "on ", "with ")):
        return False
    words_in_value = value.split()
    if len(words_in_value) < 2 and not any(suffix in value for suffix in ("inc", "llc", "ltd", "corp", "usa")):
        return False
    return True


def _ingredient_match(signal: RecallSignal, item: CatalogItem) -> list[str]:
    signal_text = compact(
        " ".join(
            [
                signal.title,
                signal.hazard_description,
                " ".join(_signal_product_names(signal)),
                " ".join(str(node) for node in signal.supplier_chain_json),
            ]
        )
    )
    matches = []
    for ingredient in item.ingredients_json:
        ingredient_text = compact(str(ingredient))
        if ingredient_text and ingredient_text in signal_text:
            matches.append(str(ingredient))
    return sorted(set(matches))


def _geography_match(signal: RecallSignal, item: CatalogItem) -> list[str]:
    states = signal.distribution_json.get("states") if isinstance(signal.distribution_json, dict) else []
    item_states = item.metadata_json.get("store_states", [])
    if not item_states:
        return []
    signal_states = {str(state).upper() for state in states}
    return sorted(signal_states & {str(state).upper() for state in item_states})


def _category_match(signal: RecallSignal, item: CatalogItem) -> str | None:
    source_text = compact(f"{signal.title} {signal.hazard_description} {' '.join(_signal_product_names(signal))}")
    category = compact(item.category)
    if category and category in source_text:
        return item.category
    return None


def _lot_missing(signal: RecallSignal) -> bool:
    identifiers = signal.identifiers_json
    return not identifiers.get("lot_codes")


def signal_lot_codes(signal: RecallSignal) -> list[str]:
    return [str(value) for value in signal.identifiers_json.get("lot_codes", [])]
