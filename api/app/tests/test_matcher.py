from api.app.models.db import CatalogItem, RecallSignal
from api.app.services.matcher import match_signal_to_catalog


def item(**overrides):
    base = {
        "id": "cat_1",
        "sku": "SKU-1",
        "brand": "Fly By Jing",
        "product_name": "Creamy Sesame Noodles Single Pack",
        "upc": "850052239886",
        "category": "instant noodles",
        "supplier_name": "Fly By Jing",
        "co_manufacturer_name": "Third-party noodle manufacturer",
        "ingredients_json": ["wheat noodles", "sesame paste", "milk powder"],
        "allergens_json": ["wheat", "soy", "sesame"],
        "supplier_aliases_json": ["Fly By Jing", "California Dairies Inc."],
        "metadata_json": {},
    }
    base.update(overrides)
    return CatalogItem(**base)


def signal(**overrides):
    base = {
        "id": "sig_1",
        "source_id": "src_1",
        "fingerprint": "fingerprint",
        "title": "Fly By Jing recalls Creamy Sesame Noodles",
        "company": "Fly By Jing",
        "hazard_type": "undeclared_allergen",
        "hazard_description": "Potential peanut cross-contact",
        "affected_products_json": [
            {
                "brand": "Fly By Jing",
                "product_name": "Creamy Sesame Noodles Single Pack",
                "upc": "850052239886",
            }
        ],
        "identifiers_json": {"upcs": ["850052239886"], "lot_codes": []},
        "supplier_chain_json": [{"name": "Third-party noodle manufacturer", "role": "co-manufacturer"}],
        "retailers_json": ["Whole Foods Market"],
        "distribution_json": {"states": ["CA", "NY"]},
        "explicit_exclusions_json": [],
        "raw_extraction_json": {},
    }
    base.update(overrides)
    return RecallSignal(**base)


def test_exact_upc_match_returns_confirmed_match():
    decisions = match_signal_to_catalog(signal(), [item()])
    assert decisions[0].tier == "confirmed_match"
    assert decisions[0].match_type == "exact_upc"


def test_brand_product_match_returns_confirmed_without_upc():
    decisions = match_signal_to_catalog(
        signal(identifiers_json={"upcs": [], "lot_codes": []}),
        [item(upc="000000000000")],
    )
    assert decisions[0].tier == "confirmed_match"
    assert decisions[0].match_type == "brand_product"


def test_brand_product_match_handles_beverage_mix_language():
    decisions = match_signal_to_catalog(
        signal(
            title="Ghirardelli recalls powdered beverage mixes",
            company="Ghirardelli Chocolate Company",
            affected_products_json=[{"product_name": "Ghirardelli Chocolate Company Powdered Beverage Mixes"}],
            identifiers_json={"upcs": [], "lot_codes": []},
        ),
        [
            item(
                brand="Ghirardelli",
                product_name="Powdered Drink Mixes",
                upc="000000000000",
                supplier_name="Ghirardelli Chocolate Company",
                supplier_aliases_json=["Ghirardelli Chocolate Company"],
            )
        ],
    )
    assert decisions[0].tier == "confirmed_match"
    assert decisions[0].match_type == "brand_product"


def test_same_brand_different_flavor_does_not_confirm_product_match():
    decisions = match_signal_to_catalog(
        signal(
            title="Zapp's potato chips recall",
            company="Utz Quality Foods",
            affected_products_json=[{"brand": "Zapp's Brand", "product_name": "Bayou Blackened Ranch Potato Chips"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            supplier_chain_json=[],
        ),
        [
            item(
                brand="Zapp's",
                product_name="Voodoo Potato Chips",
                upc="000000000000",
                category="potato chips",
                supplier_name="Utz Brands",
                co_manufacturer_name=None,
                ingredients_json=[],
                supplier_aliases_json=[],
            )
        ],
    )
    assert not any(decision.tier == "confirmed_match" for decision in decisions)


def test_product_match_from_non_recall_source_returns_watch_only():
    decisions = match_signal_to_catalog(
        signal(identifiers_json={"upcs": [], "lot_codes": []}),
        [item(upc="000000000000")],
        action_source=False,
    )
    assert decisions[0].tier == "watch_only"
    assert decisions[0].match_type == "product_mention"
    assert decisions[0].missing_fields == ["direct recall notice"]


def test_supplier_chain_overlap_returns_supplier_review():
    decisions = match_signal_to_catalog(
        signal(
            title="Powdered milk supplier recall",
            company="California Dairies Inc.",
            affected_products_json=[{"product_name": "Powdered milk ingredient"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            supplier_chain_json=[{"name": "California Dairies Inc.", "role": "ingredient supplier"}],
        ),
        [
            item(
                brand="Northstar",
                product_name="Garlic Parmesan Croutons",
                upc="744000110427",
                supplier_name="California Dairies Inc.",
                supplier_aliases_json=[],
            )
        ],
    )
    assert decisions[0].tier == "supplier_review"
    assert decisions[0].match_type == "supplier_chain"


def test_upstream_alias_only_match_stays_watch_only():
    decisions = match_signal_to_catalog(
        signal(
            title="Powdered milk supplier recall",
            company="California Dairies Inc.",
            affected_products_json=[{"product_name": "Powdered milk ingredient"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            supplier_chain_json=[{"name": "California Dairies Inc.", "role": "ingredient supplier"}],
        ),
        [
            item(
                brand="Ghirardelli",
                product_name="Double Chocolate Premium Hot Cocoa Mix",
                upc="000000000000",
                supplier_name="Ghirardelli Chocolate Company",
                supplier_aliases_json=["Ghirardelli Chocolate", "California Dairies Inc."],
            )
        ],
    )
    assert decisions[0].tier == "watch_only"
    assert decisions[0].match_type == "supplier_signal"


def test_supplier_chain_overlap_from_non_recall_source_returns_watch_only():
    decisions = match_signal_to_catalog(
        signal(
            title="Powdered milk supplier recall",
            company="California Dairies Inc.",
            affected_products_json=[{"product_name": "Powdered milk ingredient"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            supplier_chain_json=[{"name": "California Dairies Inc.", "role": "ingredient supplier"}],
        ),
        [
            item(
                brand="Northstar",
                product_name="Garlic Parmesan Croutons",
                upc="744000110427",
                supplier_name="California Dairies Inc.",
                supplier_aliases_json=[],
            )
        ],
        action_source=False,
    )
    assert decisions[0].tier == "watch_only"
    assert decisions[0].match_type == "supplier_signal"
    assert decisions[0].missing_fields == ["direct recall notice", "supplier lot confirmation"]


def test_ingredient_only_overlap_returns_watch_only():
    decisions = match_signal_to_catalog(
        signal(
            title="Powdered milk contamination alert",
            company="Unknown",
            hazard_description="Potential Salmonella in powdered milk",
            affected_products_json=[{"product_name": "powdered milk ingredient"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            supplier_chain_json=[],
        ),
        [item(supplier_aliases_json=[], co_manufacturer_name=None)],
    )
    assert decisions[0].tier == "watch_only"


def test_explicit_exclusion_returns_no_exposure():
    decisions = match_signal_to_catalog(
        signal(
            affected_products_json=[{"brand": "Fly By Jing", "product_name": "Creamy Sesame Noodles"}],
            identifiers_json={"upcs": [], "lot_codes": []},
            explicit_exclusions_json=[{"text": "No other Fly By Jing noodle flavors or sauce products are affected."}],
        ),
        [
            item(
                id="cat_sauce",
                sku="FBJ-SAUCE",
                product_name="Sichuan Chili Crisp Sauce",
                upc="111111111111",
                category="sauce",
            )
        ],
    )
    assert decisions[0].tier == "no_exposure"
    assert decisions[0].match_type == "explicit_exclusion"


def test_unrelated_product_creates_no_match():
    decisions = match_signal_to_catalog(
        signal(),
        [
            item(
                id="cat_spinach",
                sku="SPINACH",
                brand="Northstar Farms",
                product_name="Organic Baby Spinach",
                upc="222222222222",
                category="produce",
                supplier_name="Central Valley Greens",
                co_manufacturer_name=None,
                ingredients_json=["spinach"],
                supplier_aliases_json=[],
            )
        ],
    )
    assert decisions == []
