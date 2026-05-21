import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings
from api.app.models.db import CatalogItem
from api.app.repositories.catalog_repo import merge_catalog_metadata
from api.app.services.exa_client import ExaClient

PRODUCT_ASSET_TTL_DAYS = 30
PRODUCT_ASSET_LOOKUP_VERSION = "v3"


async def enrich_product_assets(
    session: AsyncSession,
    settings: Settings,
    items: list[CatalogItem],
    *,
    max_items: int = 6,
) -> int:
    if not settings.exa_configured:
        return 0

    client = ExaClient(settings)
    candidates = _items_missing_assets(items)[:max_items]
    lookups = await asyncio.gather(
        *(_lookup_asset(client, item) for item in candidates),
        return_exceptions=False,
    )

    for item, asset in zip(candidates, lookups, strict=False):
        now = datetime.now(timezone.utc)
        patch: dict[str, object] = {
            "product_image_checked_at": now.isoformat(),
            "product_image_lookup_version": PRODUCT_ASSET_LOOKUP_VERSION,
            "product_image_status": "found" if asset.get("product_image_url") else "not_found",
        }
        if not asset.get("product_image_url"):
            patch.update(_empty_asset_patch())
        patch.update(asset)
        await merge_catalog_metadata(session, item, patch)
    return len(candidates)


async def enrich_catalog_item_asset(
    session: AsyncSession,
    settings: Settings,
    item: CatalogItem,
    *,
    force: bool = False,
) -> CatalogItem:
    metadata = dict(item.metadata_json or {})
    current_version = metadata.get("product_image_lookup_version") == PRODUCT_ASSET_LOOKUP_VERSION
    if not force and current_version and _meaningful_string(metadata.get("product_image_url")):
        return item
    if not force and current_version:
        checked_at = _parse_datetime(metadata.get("product_image_checked_at"))
        if checked_at and checked_at > datetime.now(timezone.utc) - timedelta(days=PRODUCT_ASSET_TTL_DAYS):
            return item
    if not settings.exa_configured:
        return item

    asset = await _lookup_asset(ExaClient(settings), item)
    now = datetime.now(timezone.utc)
    patch: dict[str, object] = {
        "product_image_checked_at": now.isoformat(),
        "product_image_lookup_version": PRODUCT_ASSET_LOOKUP_VERSION,
        "product_image_status": "found" if asset.get("product_image_url") else "not_found",
    }
    if not asset.get("product_image_url"):
        patch.update(_empty_asset_patch())
    patch.update(asset)
    return await merge_catalog_metadata(session, item, patch)


async def _lookup_asset(client: ExaClient, item: CatalogItem) -> dict[str, str]:
    try:
        return await client.lookup_product_asset(
            brand=item.brand,
            product_name=item.product_name,
            upc=item.upc,
            category=item.category,
        )
    except Exception:
        return {}


def _items_missing_assets(items: list[CatalogItem]) -> list[CatalogItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=PRODUCT_ASSET_TTL_DAYS)
    output: list[CatalogItem] = []
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        metadata = dict(item.metadata_json or {})
        current_version = metadata.get("product_image_lookup_version") == PRODUCT_ASSET_LOOKUP_VERSION
        if current_version and _meaningful_string(metadata.get("product_image_url")):
            continue
        if not current_version:
            output.append(item)
            continue
        checked_at = _parse_datetime(metadata.get("product_image_checked_at"))
        if checked_at and checked_at > cutoff:
            continue
        output.append(item)
    return output


def _empty_asset_patch() -> dict[str, str]:
    return {
        "product_image_url": "",
        "product_image_source_url": "",
        "product_image_source_domain": "",
    }


def _meaningful_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
