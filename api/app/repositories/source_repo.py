from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import ExternalSource
from api.app.services.source_normalizer import canonicalize_url, content_hash, source_domain
from api.app.services.utils import new_id, now_utc


async def upsert_source(
    session: AsyncSession,
    url: str,
    title: str,
    source_type: str,
    published_at,
    evidence: list[str],
    raw: dict,
) -> tuple[ExternalSource, bool]:
    canonical = canonicalize_url(url)
    existing = (
        await session.execute(select(ExternalSource).where(ExternalSource.canonical_url == canonical))
    ).scalar_one_or_none()
    hashed = content_hash(title, evidence)
    if existing:
        existing.title = title or existing.title
        existing.source_type = source_type or existing.source_type
        existing.published_at = published_at or existing.published_at
        existing.last_seen_at = now_utc()
        existing.content_hash = hashed
        existing.raw_exa_result_json = raw
        await session.flush()
        return existing, False
    source = ExternalSource(
        id=new_id("src"),
        canonical_url=canonical,
        source_domain=source_domain(canonical),
        source_type=source_type,
        title=title or canonical,
        published_at=published_at,
        content_hash=hashed,
        raw_exa_result_json=raw,
    )
    session.add(source)
    await session.flush()
    return source, True

