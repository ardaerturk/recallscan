from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.models.api import SupplierLookupResponse
from api.app.repositories.supplier_repo import (
    get_supplier_profile,
    supplier_details_are_usable,
    supplier_profile_has_contact_details,
    supplier_profile_is_fresh,
    supplier_profile_payload,
    upsert_supplier_profile,
)
from api.app.services.exa_client import ExaClient

router = APIRouter()


@router.get("/suppliers/lookup", response_model=SupplierLookupResponse)
async def supplier_lookup(
    name: str = Query(min_length=2, max_length=160),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    cached = await get_supplier_profile(session, name)
    if cached and supplier_profile_is_fresh(cached) and supplier_profile_has_contact_details(cached):
        return SupplierLookupResponse(**supplier_profile_payload(cached, cache_status="hit", query=name))

    try:
        result = await ExaClient(settings).lookup_supplier(name)
    except Exception:
        if cached:
            return SupplierLookupResponse(**supplier_profile_payload(cached, cache_status="stale", query=name))
        raise

    if not supplier_details_are_usable(result.get("details") if isinstance(result.get("details"), dict) else {}):
        if cached:
            return SupplierLookupResponse(**supplier_profile_payload(cached, cache_status="stale", query=name))
        return SupplierLookupResponse(**{**result, "meta": {"cache_status": "miss_unstored"}})

    profile = await upsert_supplier_profile(session, requested_name=name, result=result)
    await session.commit()
    return SupplierLookupResponse(**supplier_profile_payload(profile, cache_status="miss", query=name))
