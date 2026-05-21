from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.services.scan_runner import run_recent_recall_scan
from api.app.services.serializers import scan_run_out

router = APIRouter()


@router.get("/jobs/scan-recent")
async def scan_recent_job(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    if not settings.cron_secret or authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    key = f"scheduled-recent-recalls:{settings.scan_query_version}:365d:{date.today().isoformat()}"
    run, source_mode = await run_recent_recall_scan(
        session,
        settings,
        days=365,
        force_fresh=False,
        idempotency_key=key,
    )
    await session.commit()
    return {"scan": scan_run_out(run), "meta": {"source_mode": source_mode, "idempotency_key": key}}
