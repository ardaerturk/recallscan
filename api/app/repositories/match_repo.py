from datetime import date, timedelta

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models.db import CatalogItem, ExposureMatch, RecallSignal
from api.app.models.domain import MatchDecision
from api.app.services.utils import new_id


async def replace_matches(
    session: AsyncSession, signal: RecallSignal, decisions: list[MatchDecision]
) -> list[ExposureMatch]:
    await session.execute(delete(ExposureMatch).where(ExposureMatch.recall_signal_id == signal.id))
    rows: list[ExposureMatch] = []
    for decision in decisions:
        row = ExposureMatch(
            id=new_id("mat"),
            recall_signal_id=signal.id,
            catalog_item_id=decision.catalog_item_id,
            tier=decision.tier,
            match_type=decision.match_type,
            matched_fields_json=decision.matched_fields,
            missing_fields_json=decision.missing_fields,
            explanation=decision.explanation,
            recommended_action=decision.recommended_action,
        )
        session.add(row)
        rows.append(row)
    await session.flush()
    return rows


async def matches_for_signal(session: AsyncSession, signal_id: str) -> list[ExposureMatch]:
    return (
        await session.execute(
            select(ExposureMatch)
            .where(ExposureMatch.recall_signal_id == signal_id)
            .order_by(ExposureMatch.tier, ExposureMatch.created_at)
        )
    ).scalars().all()


async def all_matches_for_signals(session: AsyncSession, signal_ids: list[str]) -> list[ExposureMatch]:
    if not signal_ids:
        return []
    return (
        await session.execute(select(ExposureMatch).where(ExposureMatch.recall_signal_id.in_(signal_ids)))
    ).scalars().all()


DIRECT_NOTICE_CANDIDATE_MATCH_TYPES = {
    "product_mention",
    "supplier_signal",
    "ingredient_geography",
    "nearby_category_or_ingredient",
}


async def recent_direct_notice_candidates(
    session: AsyncSession, *, days: int, limit: int = 20
) -> list[tuple[RecallSignal, CatalogItem]]:
    since = date.today() - timedelta(days=days)
    stmt = (
        select(RecallSignal, CatalogItem)
        .join(ExposureMatch, ExposureMatch.recall_signal_id == RecallSignal.id)
        .join(CatalogItem, CatalogItem.id == ExposureMatch.catalog_item_id)
        .where(
            ExposureMatch.match_type.in_(DIRECT_NOTICE_CANDIDATE_MATCH_TYPES),
            or_(RecallSignal.event_date >= since, RecallSignal.event_date.is_(None)),
        )
        .order_by(RecallSignal.event_date.desc().nullslast(), RecallSignal.updated_at.desc())
        .limit(limit)
    )
    return [(signal, item) for signal, item in (await session.execute(stmt)).all()]
