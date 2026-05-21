from datetime import datetime, timezone

from api.app.models.db import CatalogItem
from api.app.services.exa_client import _product_asset_from_search
from api.app.services.product_assets import PRODUCT_ASSET_LOOKUP_VERSION, _items_missing_assets


def catalog_item(metadata: dict[str, object] | None = None) -> CatalogItem:
    return CatalogItem(
        id="cat_test",
        sku="TEST-SKU",
        brand="Northstar",
        product_name="Test Cereal",
        category="cereal",
        supplier_name="Northstar Foods",
        ingredients_json=[],
        allergens_json=[],
        supplier_aliases_json=[],
        metadata_json=metadata or {},
    )


def test_product_asset_search_rejects_recall_source_images():
    data = {
        "output": {
            "content": {
                "page_url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/test",
                "image_url": "https://www.fda.gov/files/fda-logo.png",
                "source_domain": "fda.gov",
            }
        },
        "results": [
            {
                "url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/test",
                "image": "https://www.fda.gov/files/safety-alert.jpg",
            }
        ],
    }

    assert _product_asset_from_search(data) == {}


def test_product_asset_search_uses_product_page_image():
    data = {
        "output": {
            "content": {
                "page_url": "https://examplegrocer.com/products/northstar-test-cereal",
                "image_url": "https://cdn.examplegrocer.com/products/northstar-test-cereal.png",
                "source_domain": "examplegrocer.com",
            }
        },
        "results": [],
    }

    assert _product_asset_from_search(data) == {
        "product_image_url": "https://cdn.examplegrocer.com/products/northstar-test-cereal.png",
        "product_image_source_url": "https://examplegrocer.com/products/northstar-test-cereal",
        "product_image_source_domain": "examplegrocer.com",
    }


def test_items_missing_assets_skips_cached_product_images():
    item = catalog_item(
        {
            "product_image_url": "https://cdn.example.com/product.jpg",
            "product_image_lookup_version": PRODUCT_ASSET_LOOKUP_VERSION,
        }
    )
    assert _items_missing_assets([item]) == []


def test_items_missing_assets_retries_old_misses():
    item = catalog_item(
        {
            "product_image_checked_at": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat(),
            "product_image_lookup_version": PRODUCT_ASSET_LOOKUP_VERSION,
        }
    )
    assert _items_missing_assets([item]) == [item]


def test_items_missing_assets_retries_previous_lookup_version():
    item = catalog_item(
        {
            "product_image_url": "https://cdn.example.com/product.jpg",
            "product_image_lookup_version": "v1",
        }
    )
    assert _items_missing_assets([item]) == [item]
