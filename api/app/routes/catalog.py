from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.models.api import ProductAssetOut
from api.app.repositories.catalog_repo import get_catalog_item, list_catalog_items, ensure_catalog_bootstrap
from api.app.services.product_assets import enrich_catalog_item_asset
from api.app.services.serializers import catalog_item_out

router = APIRouter()


@router.get("/catalog")
async def catalog(session: AsyncSession = Depends(get_session)):
    await ensure_catalog_bootstrap(session)
    await session.commit()
    items = await list_catalog_items(session)
    return {"items": [catalog_item_out(item) for item in items]}


@router.get("/catalog/{catalog_item_id}")
async def catalog_item(catalog_item_id: str, session: AsyncSession = Depends(get_session)):
    item = await get_catalog_item(session, catalog_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    return catalog_item_out(item)


@router.get("/catalog/{catalog_item_id}/asset", response_model=ProductAssetOut)
async def catalog_item_asset(
    catalog_item_id: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    item = await get_catalog_item(session, catalog_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    item = await enrich_catalog_item_asset(session, settings, item)
    await session.commit()
    metadata = dict(item.metadata_json or {})
    return ProductAssetOut(
        catalog_item_id=item.id,
        product_image_url=_asset_value(metadata, "product_image_url"),
        product_image_source_url=_asset_value(metadata, "product_image_source_url"),
        product_image_source_domain=_asset_value(metadata, "product_image_source_domain"),
        status=_asset_value(metadata, "product_image_status") or "not_found",
    )


def _asset_value(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None
