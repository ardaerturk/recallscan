from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import ScanRun
from api.app.services.utils import new_id, now_utc


async def create_scan_run(
    session: AsyncSession, scan_type: str, query_version: str, idempotency_key: str | None = None
) -> ScanRun:
    run = ScanRun(
        id=new_id("scan"),
        scan_type=scan_type,
        status="running",
        query_version=query_version,
        idempotency_key=idempotency_key,
    )
    session.add(run)
    await session.flush()
    return run


async def get_scan_run_by_idempotency_key(
    session: AsyncSession, idempotency_key: str
) -> ScanRun | None:
    return (
        await session.execute(select(ScanRun).where(ScanRun.idempotency_key == idempotency_key))
    ).scalar_one_or_none()


async def restart_failed_scan_run(session: AsyncSession, run: ScanRun) -> ScanRun:
    run.status = "running"
    run.started_at = now_utc()
    run.finished_at = None
    run.error_message = None
    run.sources_found = 0
    run.signals_created = 0
    run.signals_updated = 0
    run.matches_created = 0
    await session.flush()
    return run


async def finish_scan_run(
    session: AsyncSession,
    run: ScanRun,
    status: str,
    sources_found: int = 0,
    signals_created: int = 0,
    signals_updated: int = 0,
    matches_created: int = 0,
    error_message: str | None = None,
) -> ScanRun:
    run.status = status
    run.finished_at = now_utc()
    run.sources_found = sources_found
    run.signals_created = signals_created
    run.signals_updated = signals_updated
    run.matches_created = matches_created
    run.error_message = error_message
    await session.flush()
    return run


async def recent_scan_runs(session: AsyncSession, limit: int = 6) -> list[ScanRun]:
    return (
        await session.execute(select(ScanRun).order_by(ScanRun.started_at.desc()).limit(limit))
    ).scalars().all()


async def last_successful_scan_at(session: AsyncSession):
    run = (
        await session.execute(
            select(ScanRun)
            .where(ScanRun.status == "completed")
            .order_by(ScanRun.finished_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return run.finished_at if run else None
