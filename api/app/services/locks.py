from datetime import timedelta

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import JobLock
from api.app.services.utils import now_utc


async def acquire_lock(session: AsyncSession, name: str, owner_id: str, ttl_seconds: int = 180) -> bool:
    now = now_utc()
    expires_at = now + timedelta(seconds=ttl_seconds)
    statement = (
        insert(JobLock)
        .values(name=name, owner_id=owner_id, expires_at=expires_at, created_at=now)
        .on_conflict_do_update(
            index_elements=[JobLock.name],
            set_={"owner_id": owner_id, "expires_at": expires_at, "created_at": now},
            where=JobLock.expires_at <= now,
        )
        .returning(JobLock.name)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None


async def release_lock(session: AsyncSession, name: str, owner_id: str) -> None:
    current = await session.get(JobLock, name)
    if current and current.owner_id == owner_id:
        await session.delete(current)
        await session.flush()
