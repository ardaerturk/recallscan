from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import get_settings
from api.app.models.api import (
    CatalogItemOut,
    ExposureMatchOut,
    RecallSignalOut,
    ScanRunOut,
    SourceOut,
)
from api.app.models.db import CatalogItem, ExposureMatch, ExternalSource, RecallSignal, ScanRun
from api.app.repositories.catalog_repo import inventory_for_catalog_item
from api.app.repositories.match_repo import all_matches_for_signals
from api.app.services.action_memo import build_action_memo
from api.app.services.matcher import signal_lot_codes


def catalog_item_out(item: CatalogItem) -> CatalogItemOut:
    return CatalogItemOut(
        id=item.id,
        sku=item.sku,
        brand=item.brand,
        product_name=item.product_name,
        upc=item.upc,
        category=item.category,
        supplier_name=item.supplier_name,
        co_manufacturer_name=item.co_manufacturer_name,
        ingredients=list(item.ingredients_json or []),
        allergens=list(item.allergens_json or []),
        supplier_aliases=list(item.supplier_aliases_json or []),
        metadata=dict(item.metadata_json or {}),
    )


def scan_run_out(run: ScanRun) -> ScanRunOut:
    return ScanRunOut(
        id=run.id,
        scan_type=run.scan_type,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_message=run.error_message,
        sources_found=run.sources_found,
        signals_created=run.signals_created,
        signals_updated=run.signals_updated,
        matches_created=run.matches_created,
    )


async def signal_outputs(session: AsyncSession, signals: list[RecallSignal]) -> list[RecallSignalOut]:
    signals = _dedupe_signals_by_source(signals)
    if not signals:
        return []
    signal_ids = [signal.id for signal in signals]
    matches = await all_matches_for_signals(session, signal_ids)
    by_signal: dict[str, list[ExposureMatch]] = defaultdict(list)
    for match in matches:
        by_signal[match.recall_signal_id].append(match)

    item_ids = list({match.catalog_item_id for match in matches})
    item_map: dict[str, CatalogItem] = {}
    if item_ids:
        items = (await session.execute(select(CatalogItem).where(CatalogItem.id.in_(item_ids)))).scalars().all()
        item_map = {item.id: item for item in items}

    outputs = []
    for signal in signals:
        outputs.append(await signal_out(session, signal, by_signal.get(signal.id, []), item_map))
    return outputs


def _dedupe_signals_by_source(signals: list[RecallSignal]) -> list[RecallSignal]:
    by_source: dict[str, RecallSignal] = {}
    for signal in signals:
        current = by_source.get(signal.source_id)
        if current is None or signal.updated_at > current.updated_at:
            by_source[signal.source_id] = signal
    return [signal for signal in signals if by_source.get(signal.source_id) is signal]


async def signal_out(
    session: AsyncSession,
    signal: RecallSignal,
    matches: list[ExposureMatch] | None = None,
    item_map: dict[str, CatalogItem] | None = None,
) -> RecallSignalOut:
    matches = matches if matches is not None else []
    item_map = item_map if item_map is not None else {}
    if not matches:
        matches = (
            await session.execute(select(ExposureMatch).where(ExposureMatch.recall_signal_id == signal.id))
        ).scalars().all()
        if matches and not item_map:
            item_ids = [match.catalog_item_id for match in matches]
            items = (await session.execute(select(CatalogItem).where(CatalogItem.id.in_(item_ids)))).scalars().all()
            item_map = {item.id: item for item in items}

    match_outputs = []
    lot_codes = signal_lot_codes(signal)
    states = signal.distribution_json.get("states", []) if isinstance(signal.distribution_json, dict) else []
    for match in matches:
        item = item_map.get(match.catalog_item_id)
        if not item:
            continue
        impacted = await inventory_for_catalog_item(
            session,
            item.id,
            lot_codes=lot_codes if match.tier == "confirmed_match" else None,
            states=states if match.tier in {"confirmed_match", "watch_only"} else None,
        )
        if not impacted:
            impacted = await inventory_for_catalog_item(session, item.id)
        match_outputs.append(
            ExposureMatchOut(
                id=match.id,
                catalog_item=catalog_item_out(item),
                tier=match.tier,
                match_type=match.match_type,
                matched_fields=match.matched_fields_json,
                missing_fields=match.missing_fields_json,
                explanation=match.explanation,
                recommended_action=match.recommended_action,
                impacted_inventory=impacted,
            )
        )

    source = signal.__dict__.get("source") or await session.get(ExternalSource, signal.source_id)
    if not source:
        raise RuntimeError(f"Missing source for signal {signal.id}")
    settings = get_settings()
    raw_source = source.raw_exa_result_json if settings.debug_raw_sources else {}
    evidence = signal.raw_extraction_json.get("evidence", [])
    return RecallSignalOut(
        id=signal.id,
        title=signal.title,
        company=signal.company,
        hazard_type=signal.hazard_type,
        hazard_description=signal.hazard_description,
        affected_products=signal.affected_products_json,
        identifiers=signal.identifiers_json,
        supplier_chain=signal.supplier_chain_json,
        retailers=signal.retailers_json,
        distribution=signal.distribution_json,
        explicit_exclusions=signal.explicit_exclusions_json,
        event_date=signal.event_date,
        source=SourceOut(
            id=source.id,
            canonical_url=source.canonical_url,
            source_domain=source.source_domain,
            source_type=source.source_type,
            title=source.title,
            image_url=_string_or_none(source.raw_exa_result_json.get("image")),
            favicon_url=_string_or_none(source.raw_exa_result_json.get("favicon")),
            image_links=_image_links(source.raw_exa_result_json),
            published_at=source.published_at,
            first_seen_at=source.first_seen_at,
            last_seen_at=source.last_seen_at,
            raw_exa_result=raw_source,
        ),
        matches=match_outputs,
        evidence=evidence if isinstance(evidence, list) else [],
        action_memo=build_action_memo(signal, matches),
    )


def _string_or_none(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _image_links(raw: dict[str, object]) -> list[str]:
    extras = raw.get("extras")
    if not isinstance(extras, dict):
        return []
    values = extras.get("imageLinks")
    if not isinstance(values, list):
        return []
    return [value.strip() for value in values if isinstance(value, str) and value.strip()]
