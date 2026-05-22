from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _sql() -> str:
    return "\n".join(path.read_text() for path in sorted(MIGRATIONS_DIR.glob("*.sql")))


def test_inventory_store_references_are_seeded() -> None:
    sql = _sql()
    seeded_stores = set(re.findall(r"\('((?:store_)[^']+)',\s*'Northstar Market", sql))
    inventory_stores = set(re.findall(r"\('lot_[^']+',\s*'cat_[^']+',\s*'(store_[^']+)'", sql))

    assert inventory_stores <= seeded_stores


def test_inventory_catalog_references_are_seeded() -> None:
    sql = _sql()
    seeded_items = set(re.findall(r"\(\s*'(cat_[^']+)',\s*'[A-Z0-9]", sql))
    inventory_items = set(re.findall(r"\('lot_[^']+',\s*'(cat_[^']+)'", sql))

    assert inventory_items <= seeded_items
