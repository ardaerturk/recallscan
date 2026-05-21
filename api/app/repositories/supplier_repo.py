import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import SupplierProfile

SUPPLIER_PROFILE_TTL_DAYS = 30


def normalize_supplier_name(name: str) -> str:
    value = name.lower().strip()
    value = value.replace("&", " and ")
    value = re.sub(r"\b(incorporated|corporation|company|limited|llc|inc|corp|ltd|co)\b\.?", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


async def get_supplier_profile(session: AsyncSession, name: str) -> SupplierProfile | None:
    normalized = normalize_supplier_name(name)
    if not normalized:
        return None
    return await session.get(SupplierProfile, normalized)


def supplier_profile_is_fresh(profile: SupplierProfile, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    expires_at = profile.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > now


def supplier_profile_has_contact_details(profile: SupplierProfile) -> bool:
    return supplier_details_are_usable(dict(profile.details_json or {}))


def supplier_details_are_usable(details: dict[str, Any]) -> bool:
    return any(
        _meaningful_text(details.get(key))
        for key in ("phone", "email", "address", "website", "recall_or_quality_contact")
    )


def _meaningful_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    return bool(text and text not in {"unknown", "none", "null", "n/a", "not available"})


async def upsert_supplier_profile(
    session: AsyncSession,
    *,
    requested_name: str,
    result: dict[str, Any],
    ttl_days: int = SUPPLIER_PROFILE_TTL_DAYS,
) -> SupplierProfile:
    normalized = normalize_supplier_name(requested_name)
    now = datetime.now(timezone.utc)
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    display_name = str(details.get("company_name") or requested_name).strip()
    values = {
        "normalized_name": normalized,
        "display_name": display_name or requested_name,
        "details_json": details,
        "sources_json": result.get("sources") if isinstance(result.get("sources"), list) else [],
        "fetched_at": now,
        "expires_at": now + timedelta(days=ttl_days),
        "updated_at": now,
    }
    stmt = insert(SupplierProfile).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[SupplierProfile.normalized_name],
        set_={
            "display_name": stmt.excluded.display_name,
            "details_json": stmt.excluded.details_json,
            "sources_json": stmt.excluded.sources_json,
            "fetched_at": stmt.excluded.fetched_at,
            "expires_at": stmt.excluded.expires_at,
            "updated_at": stmt.excluded.updated_at,
        },
    ).returning(SupplierProfile)
    return (await session.execute(stmt)).scalar_one()


def supplier_profile_payload(profile: SupplierProfile, *, cache_status: str, query: str | None = None) -> dict[str, Any]:
    return {
        "query": query or profile.display_name,
        "details": dict(profile.details_json or {}),
        "sources": list(profile.sources_json or []),
        "meta": {
            "cache_status": cache_status,
            "fetched_at": profile.fetched_at.isoformat(),
            "expires_at": profile.expires_at.isoformat(),
        },
    }
