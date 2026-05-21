from datetime import timedelta
from hashlib import sha256
import json
from typing import Literal

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import IdempotencyKey
from api.app.services.utils import now_utc


def request_hash(payload: object) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(body.encode("utf-8")).hexdigest()


async def read_idempotent_response(
    session: AsyncSession, key: str, payload_hash: str
) -> tuple[int, dict] | str | None:
    row = await session.get(IdempotencyKey, key)
    if not row:
        return None
    if row.expires_at < now_utc():
        await session.delete(row)
        await session.flush()
        return None
    if row.request_hash != payload_hash:
        return "conflict"
    if row.response_json.get("state") == "processing":
        return "processing"
    return row.status_code, row.response_json


async def claim_idempotency_key(
    session: AsyncSession, key: str, payload_hash: str
) -> Literal["claimed", "conflict", "processing"] | tuple[int, dict]:
    expires = now_utc() + timedelta(hours=24)
    statement = (
        insert(IdempotencyKey)
        .values(
            key=key,
            request_hash=payload_hash,
            response_json={"state": "processing"},
            status_code=202,
            expires_at=expires,
        )
        .on_conflict_do_nothing(index_elements=[IdempotencyKey.key])
        .returning(IdempotencyKey.key)
    )
    inserted = (await session.execute(statement)).scalar_one_or_none()
    if inserted:
        await session.flush()
        return "claimed"

    row = await session.get(IdempotencyKey, key)
    if not row:
        return "claimed"
    if row.expires_at < now_utc():
        await session.delete(row)
        await session.flush()
        session.add(
            IdempotencyKey(
                key=key,
                request_hash=payload_hash,
                response_json={"state": "processing"},
                status_code=202,
                expires_at=expires,
            )
        )
        await session.flush()
        return "claimed"
    if row.request_hash != payload_hash:
        return "conflict"
    if row.response_json.get("state") == "processing":
        return "processing"
    return row.status_code, row.response_json


async def store_idempotent_response(
    session: AsyncSession, key: str, payload_hash: str, status_code: int, response: dict
) -> None:
    existing = await session.get(IdempotencyKey, key)
    expires = now_utc() + timedelta(hours=24)
    if existing:
        existing.request_hash = payload_hash
        existing.response_json = response
        existing.status_code = status_code
        existing.expires_at = expires
    else:
        session.add(
            IdempotencyKey(
                key=key,
                request_hash=payload_hash,
                response_json=response,
                status_code=status_code,
                expires_at=expires,
            )
        )
    await session.flush()


async def clear_idempotency_key(session: AsyncSession, key: str) -> None:
    row = await session.get(IdempotencyKey, key)
    if row:
        await session.delete(row)
        await session.flush()


async def purge_expired_idempotency_keys(session: AsyncSession) -> int:
    result = await session.execute(delete(IdempotencyKey).where(IdempotencyKey.expires_at < now_utc()))
    await session.flush()
    return result.rowcount or 0
