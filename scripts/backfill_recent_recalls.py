import asyncio

from api.app.config import get_settings
from api.app.db import SessionLocal, ensure_schema
from api.app.services.scan_runner import run_recent_recall_scan


async def main() -> None:
    await ensure_schema()
    async with SessionLocal() as session:
        run, source_mode = await run_recent_recall_scan(
            session,
            get_settings(),
            days=365,
            force_fresh=False,
            idempotency_key="manual-backfill-recent-recalls-365d",
        )
        await session.commit()
        print({"scan_id": run.id, "status": run.status, "source_mode": source_mode})


if __name__ == "__main__":
    asyncio.run(main())
