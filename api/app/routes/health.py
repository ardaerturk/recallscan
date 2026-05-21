from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.repositories.scan_repo import last_successful_scan_at

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)):
    db_ok = True
    try:
        await session.execute(text("select 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "unavailable",
        "exa_key_configured": settings.exa_configured,
        "last_successful_scan_at": await last_successful_scan_at(session) if db_ok else None,
    }

