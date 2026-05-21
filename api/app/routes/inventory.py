from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db import get_session
from api.app.repositories.catalog_repo import catalog_summary, inventory_for_catalog_item, ensure_catalog_bootstrap

router = APIRouter()


@router.get("/inventory/summary")
async def inventory_summary(session: AsyncSession = Depends(get_session)):
    await ensure_catalog_bootstrap(session)
    await session.commit()
    return await catalog_summary(session)


@router.get("/inventory/catalog-item/{catalog_item_id}")
async def inventory_for_item(catalog_item_id: str, session: AsyncSession = Depends(get_session)):
    return {"lots": await inventory_for_catalog_item(session, catalog_item_id)}
