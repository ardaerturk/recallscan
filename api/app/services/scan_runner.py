from sqlalchemy.ext.asyncio import AsyncSession

from api.app.config import Settings
from api.app.models.db import ExternalSource
from api.app.repositories.catalog_repo import list_catalog_items, ensure_catalog_bootstrap
from api.app.repositories.match_repo import recent_direct_notice_candidates, replace_matches
from api.app.repositories.scan_repo import (
    create_scan_run,
    finish_scan_run,
    get_scan_run_by_idempotency_key,
    restart_failed_scan_run,
)
from api.app.repositories.signal_repo import recent_signals, upsert_signal
from api.app.repositories.source_repo import upsert_source
from api.app.services.locks import acquire_lock, release_lock
from api.app.services.matcher import match_signal_to_catalog
from api.app.services.product_assets import enrich_product_assets
from api.app.services.recall_discovery import (
    DirectRecallNoticeCandidate,
    discover_direct_recall_notice_sources,
    discover_recent_recall_sources,
    parse_published_at,
)
from api.app.services.recall_extraction import extract_from_exa_result
from api.app.services.signal_normalizer import normalize_signal
from api.app.services.source_classification import classify_source, is_action_source_type
from api.app.services.utils import new_id


async def run_recent_recall_scan(
    session: AsyncSession,
    settings: Settings,
    *,
    days: int,
    force_fresh: bool = False,
    idempotency_key: str | None = None,
    source_limit: int | None = None,
    direct_notice_max_items: int = 3,
    product_asset_max_items: int = 2,
) -> tuple[object, str]:
    await ensure_catalog_bootstrap(session)
    existing_run = (
        await get_scan_run_by_idempotency_key(session, idempotency_key) if idempotency_key else None
    )
    if existing_run and existing_run.status != "failed":
        return existing_run, "idempotent_replay"

    owner_id = new_id("owner")
    lock_acquired = await acquire_lock(session, "recent-recall-scan", owner_id)
    if not lock_acquired:
        existing_key_is_failed = existing_run is not None and existing_run.status == "failed"
        run = await create_scan_run(
            session,
            "recent_recalls",
            settings.scan_query_version,
            None if existing_key_is_failed else idempotency_key,
        )
        await finish_scan_run(session, run, "already_running")
        return run, "already_running"

    run = (
        await restart_failed_scan_run(session, existing_run)
        if existing_run and existing_run.status == "failed"
        else await create_scan_run(
            session, "recent_recalls", settings.scan_query_version, idempotency_key
        )
    )
    source_mode = "unknown"
    sources_found = 0
    signals_created = 0
    signals_updated = 0
    matches_created = 0
    try:
        raw_results, source_mode = await discover_recent_recall_sources(
            settings, days=days, force_fresh=force_fresh
        )
        if source_limit is not None:
            raw_results = raw_results[:source_limit]
        catalog = await list_catalog_items(session)
        catalog_by_id = {item.id: item for item in catalog}
        matched_catalog_item_ids: list[str] = []
        seen_catalog_item_ids: set[str] = set()
        direct_notice_candidates: list[DirectRecallNoticeCandidate] = []
        processed_urls: set[str] = set()
        for raw in raw_results:
            processed_urls.add(str(raw.get("url") or ""))
            result = await _process_raw_result(session, raw, catalog)
            signals_created += 1 if result.created else 0
            signals_updated += 0 if result.created else 1
            matches_created += result.matches_created
            sources_found += 1
            for item_id in result.matched_catalog_item_ids:
                if item_id not in seen_catalog_item_ids:
                    matched_catalog_item_ids.append(item_id)
                    seen_catalog_item_ids.add(item_id)
            direct_notice_candidates.extend(result.direct_notice_candidates)

        if direct_notice_max_items > 0:
            direct_results, direct_mode = await discover_direct_recall_notice_sources(
                settings,
                [
                    *(await _stored_direct_notice_candidates(session, days=days)),
                    *direct_notice_candidates,
                ],
                days=days,
                force_fresh=force_fresh,
                max_items=direct_notice_max_items,
            )
            if direct_results:
                source_mode = f"{source_mode}+{direct_mode}"
            for raw in direct_results:
                url = str(raw.get("url") or "")
                if not url or url in processed_urls:
                    continue
                processed_urls.add(url)
                result = await _process_raw_result(session, raw, catalog)
                signals_created += 1 if result.created else 0
                signals_updated += 0 if result.created else 1
                matches_created += result.matches_created
                sources_found += 1
                for item_id in result.matched_catalog_item_ids:
                    if item_id not in seen_catalog_item_ids:
                        matched_catalog_item_ids.append(item_id)
                        seen_catalog_item_ids.add(item_id)
        matched_items = [catalog_by_id[item_id] for item_id in matched_catalog_item_ids if item_id in catalog_by_id]
        if product_asset_max_items > 0:
            await enrich_product_assets(session, settings, matched_items, max_items=product_asset_max_items)
        matches_created = await _refresh_recent_exposure_matches(session, catalog, days=days)
        await finish_scan_run(
            session,
            run,
            "completed",
            sources_found=sources_found,
            signals_created=signals_created,
            signals_updated=signals_updated,
            matches_created=matches_created,
        )
        return run, source_mode
    except Exception as exc:
        await finish_scan_run(session, run, "failed", error_message=str(exc))
        raise
    finally:
        await release_lock(session, "recent-recall-scan", owner_id)


class ProcessedScanResult:
    def __init__(
        self,
        *,
        created: bool,
        matches_created: int,
        matched_catalog_item_ids: list[str],
        direct_notice_candidates: list[DirectRecallNoticeCandidate],
    ) -> None:
        self.created = created
        self.matches_created = matches_created
        self.matched_catalog_item_ids = matched_catalog_item_ids
        self.direct_notice_candidates = direct_notice_candidates


async def _process_raw_result(session: AsyncSession, raw: dict, catalog: list) -> ProcessedScanResult:
    catalog_by_id = {item.id: item for item in catalog}
    evidence = _evidence(raw)
    source_type = raw.get("source_type") or classify_source(
        str(raw.get("url") or ""),
        str(raw.get("title") or ""),
    )
    source, _ = await upsert_source(
        session,
        url=raw["url"],
        title=raw.get("title") or raw["url"],
        source_type=source_type,
        published_at=parse_published_at(raw.get("publishedDate") or raw.get("published_date")),
        evidence=evidence,
        raw=raw,
    )
    normalized = normalize_signal(extract_from_exa_result(raw))
    row, created = await upsert_signal(session, source, normalized)
    decisions = match_signal_to_catalog(row, catalog, action_source=is_action_source_type(source.source_type))
    created_matches = await replace_matches(session, row, decisions)
    return ProcessedScanResult(
        created=created,
        matches_created=len(created_matches),
        matched_catalog_item_ids=[decision.catalog_item_id for decision in decisions],
        direct_notice_candidates=[
            DirectRecallNoticeCandidate(
                item=catalog_by_id[decision.catalog_item_id],
                context=_direct_notice_context(row),
            )
            for decision in decisions
            if decision.match_type
            in {
                "product_mention",
                "supplier_signal",
                "ingredient_geography",
                "nearby_category_or_ingredient",
            }
            and not is_action_source_type(source.source_type)
            and decision.catalog_item_id in catalog_by_id
        ],
    )


async def _refresh_recent_exposure_matches(session: AsyncSession, catalog: list, *, days: int) -> int:
    total = 0
    for signal in await recent_signals(session, days=days):
        source = await session.get(ExternalSource, signal.source_id)
        if not source:
            continue
        decisions = match_signal_to_catalog(signal, catalog, action_source=is_action_source_type(source.source_type))
        total += len(await replace_matches(session, signal, decisions))
    return total


def _evidence(raw: dict) -> list[str]:
    highlights = raw.get("highlights", [])
    output = []
    for highlight in highlights:
        if isinstance(highlight, str):
            output.append(highlight)
        elif isinstance(highlight, dict):
            text = highlight.get("text") or highlight.get("highlight")
            if text:
                output.append(str(text))
    if raw.get("summary") and not _looks_like_structured_json(raw["summary"]):
        output.append(str(raw["summary"]))
    return output


def _direct_notice_context(signal) -> str:
    product_names = [
        str(product.get("product_name") or product.get("name") or "")
        for product in signal.affected_products_json
        if isinstance(product, dict)
    ]
    values = [signal.title, signal.company or "", *product_names, signal.hazard_description]
    return " ".join(value for value in values if value).strip()


async def _stored_direct_notice_candidates(session: AsyncSession, *, days: int) -> list[DirectRecallNoticeCandidate]:
    return [
        DirectRecallNoticeCandidate(item=item, context=_direct_notice_context(signal))
        for signal, item in await recent_direct_notice_candidates(session, days=days)
    ]


def _looks_like_structured_json(value: object) -> bool:
    if isinstance(value, dict):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    return text.startswith("{") or text.startswith("[")
