from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import ExternalSource, RecallSignal
from api.app.models.domain import NormalizedRecallSignal
from api.app.services.utils import new_id, now_utc


async def upsert_signal(
    session: AsyncSession, source: ExternalSource, signal: NormalizedRecallSignal
) -> tuple[RecallSignal, bool]:
    existing = (
        await session.execute(select(RecallSignal).where(RecallSignal.fingerprint == signal.fingerprint))
    ).scalar_one_or_none()
    if existing:
        existing.source_id = source.id
        existing.title = signal.title
        existing.company = signal.company
        existing.hazard_type = signal.hazard_type
        existing.hazard_description = signal.hazard_description
        existing.affected_products_json = signal.affected_products
        existing.identifiers_json = signal.identifiers
        existing.supplier_chain_json = signal.supplier_chain
        existing.retailers_json = signal.retailers
        existing.distribution_json = signal.distribution
        existing.explicit_exclusions_json = signal.explicit_exclusions
        existing.event_date = signal.event_date
        existing.raw_extraction_json = signal.raw_extraction
        existing.updated_at = now_utc()
        await session.flush()
        return existing, False
    row = RecallSignal(
        id=new_id("sig"),
        source_id=source.id,
        fingerprint=signal.fingerprint,
        title=signal.title,
        company=signal.company,
        hazard_type=signal.hazard_type,
        hazard_description=signal.hazard_description,
        affected_products_json=signal.affected_products,
        identifiers_json=signal.identifiers,
        supplier_chain_json=signal.supplier_chain,
        retailers_json=signal.retailers,
        distribution_json=signal.distribution,
        explicit_exclusions_json=signal.explicit_exclusions,
        event_date=signal.event_date,
        raw_extraction_json=signal.raw_extraction,
    )
    session.add(row)
    await session.flush()
    return row, True


async def recent_signals(session: AsyncSession, days: int = 365) -> list[RecallSignal]:
    since = date.today() - timedelta(days=days)
    stmt = (
        select(RecallSignal)
        .where(or_(RecallSignal.event_date >= since, RecallSignal.event_date.is_(None)))
        .order_by(RecallSignal.event_date.desc().nullslast(), RecallSignal.created_at.desc())
    )
    return (await session.execute(stmt)).scalars().all()
