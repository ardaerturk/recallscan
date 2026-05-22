import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.repositories.scan_repo import last_successful_scan_at

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session), settings: Settings = Depends(get_settings)):
    db_ok = True
    last_scan = None
    try:
        await session.execute(text("select 1"))
        last_scan = await last_successful_scan_at(session)
    except Exception:
        logger.exception("Database health check failed")
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "unavailable",
        "exa_key_configured": settings.exa_configured,
        "last_successful_scan_at": last_scan,
    }
