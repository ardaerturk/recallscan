import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")

from api.app.config import Settings
from api.app.repositories.supplier_repo import normalize_supplier_name
from api.app.services.idempotency import request_hash
from api.app.services.recall_discovery import discover_recent_recall_sources
from api.app.services.recall_extraction import extract_from_exa_result
from api.app.services.source_normalizer import canonicalize_url, is_aggregate_source_url


def test_canonical_url_removes_tracking_params_and_fragments():
    assert (
        canonicalize_url("https://www.fda.gov/recalls/example/?utm_source=x&permalink=abc&id=42#section")
        == "https://www.fda.gov/recalls/example?id=42"
    )


def test_aggregate_source_urls_are_identified():
    assert is_aggregate_source_url(
        "https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information?utm_source=x"
    )
    assert is_aggregate_source_url(
        "https://fda.gov/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements"
    )
    assert is_aggregate_source_url(
        "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls"
    )
    assert not is_aggregate_source_url(
        "https://www.fda.gov/food/outbreaks-foodborne-illness/outbreak-investigation-salmonella-eggs-june-2025"
    )


def test_request_hash_is_stable_for_key_order():
    left = request_hash({"days": 365, "force_fresh": False})
    right = request_hash({"force_fresh": False, "days": 365})
    assert left == right


def test_supplier_profile_cache_key_normalizes_company_suffixes():
    assert normalize_supplier_name("Sugar Foods LLC") == normalize_supplier_name("Sugar Foods Corporation")
    assert normalize_supplier_name("John B. Sanfilippo & Son, Inc.") == "john b sanfilippo and son"


def test_exa_contents_structured_summary_drives_extraction():
    extracted = extract_from_exa_result(
        {
            "url": "https://www.fda.gov/example",
            "title": "Recall notice",
            "summary": """
            {
              "title": "Fly By Jing recalls Creamy Sesame Noodles",
              "company": "Fly By Jing",
              "hazard_type": "undeclared_allergen",
              "hazard_description": "Undeclared peanut cross-contact",
              "affected_products": [
                {
                  "brand": "Fly By Jing",
                  "product_name": "Creamy Sesame Noodles Single Pack",
                  "upc": "850052239886",
                  "lot_codes": ["L0426"]
                }
              ],
              "upcs": ["850052239886"],
              "lot_codes": ["L0426"],
              "supplier_chain": [{"name": "Third-party noodle manufacturer", "role": "co-manufacturer"}],
              "explicit_exclusions": [{"text": "No sauce products are affected."}]
            }
            """,
        }
    )

    assert extracted["title"] == "Fly By Jing recalls Creamy Sesame Noodles"
    assert extracted["upcs"] == ["850052239886"]
    assert extracted["lot_codes"] == ["L0426"]
    assert extracted["explicit_exclusions"][0]["text"] == "No sauce products are affected."


def test_recall_announcement_title_extracts_affected_product():
    extracted = extract_from_exa_result(
        {
            "url": "https://example.com/recall",
            "title": "Sugar Foods Issues Recall of Specific Lots of Kroger Homestyle Cheese Garlic Croutons Due to Possible Health Risk",
        }
    )

    assert extracted["affected_products"] == [{"product_name": "Kroger Homestyle Cheese Garlic Croutons"}]


def test_recall_prose_can_extract_supplier_chain():
    extracted = extract_from_exa_result(
        {
            "url": "https://example.com/croutons",
            "title": "Kroger Cheese Garlic Croutons Recall",
            "highlights": [
                (
                    "The affected milk powder was supplied by California Dairies, Inc. to Solina USA, "
                    "which manufactures the seasoning blend. That finished seasoning is then sold to "
                    "Sugar Foods and applied to the croutons."
                )
            ],
        }
    )

    assert extracted["supplier_chain"] == [
        {"name": "California Dairies, Inc", "role": "ingredient supplier"},
        {"name": "Solina USA", "role": "processor"},
        {"name": "Sugar Foods", "role": "downstream manufacturer"},
    ]


@pytest.mark.asyncio
async def test_discovery_requires_exa_key_without_canned_data():
    settings = Settings(exa_api_key=None, database_url="postgresql://user:pass@localhost:5432/test")

    with pytest.raises(RuntimeError, match="EXA_API_KEY"):
        await discover_recent_recall_sources(settings, days=365)
