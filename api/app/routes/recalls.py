from asyncpg.exceptions import PostgresError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings, get_settings
from api.app.db import get_session
from api.app.models.api import DashboardResponse
from api.app.repositories.catalog_repo import catalog_summary, ensure_catalog_bootstrap
from api.app.repositories.scan_repo import recent_scan_runs
from api.app.repositories.signal_repo import recent_signals
from api.app.services.scan_runner import run_recent_recall_scan
from api.app.services.serializers import scan_run_out, signal_outputs

router = APIRouter()


@router.get("/recalls/recent", response_model=DashboardResponse)
async def recent_recalls(
    days: int = 365,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    try:
        await ensure_catalog_bootstrap(session)
        await session.commit()
        signals = await recent_signals(session, days=days)
        source_mode = "database"
        if not signals:
            _, source_mode = await run_recent_recall_scan(
                session,
                settings,
                days=days,
                force_fresh=False,
                source_limit=16,
                direct_notice_max_items=0,
                product_asset_max_items=0,
            )
            await session.commit()
            signals = await recent_signals(session, days=days)

        scans = await recent_scan_runs(session)
        return DashboardResponse(
            catalog_summary=await catalog_summary(session),
            signals=await signal_outputs(session, signals),
            scan_history=[scan_run_out(run) for run in scans],
            meta={
                "source_mode": source_mode,
                "days": days,
            },
        )
    except (SQLAlchemyError, PostgresError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Check the Neon connection and project quota.",
        ) from exc
