import asyncio
from dataclasses import dataclass
from datetime import datetime

from api.app.config import Settings
from api.app.models.db import CatalogItem
from api.app.services.exa_client import ExaClient
from api.app.services.source_normalizer import is_aggregate_source_url


@dataclass(frozen=True)
class DirectRecallNoticeCandidate:
    item: CatalogItem
    context: str = ""


async def discover_recent_recall_sources(
    settings: Settings, *, days: int, force_fresh: bool = False
) -> tuple[list[dict], str]:
    if not settings.exa_configured:
        raise RuntimeError("EXA_API_KEY is required to scan live recall sources.")

    client = ExaClient(settings)
    results = [
        result
        for result in await client.search_recent_recalls(days=days, force_fresh=force_fresh)
        if not is_aggregate_source_url(str(result.get("url") or ""))
    ]

    if not results:
        return [], "exa_live_empty"

    urls = [item["url"] for item in results if item.get("url")][:16]
    try:
        content_results = await client.get_contents(urls, force_fresh=force_fresh)
    except Exception:
        return results, "exa_live_search_only"

    by_url = {item.get("url"): item for item in results if item.get("url")}
    for content in content_results:
        url = content.get("url")
        if url and url in by_url:
            by_url[url].update({key: value for key, value in content.items() if value})

    return list(by_url.values()), "exa_live"


async def discover_direct_recall_notice_sources(
    settings: Settings,
    candidates: list[DirectRecallNoticeCandidate],
    *,
    days: int,
    force_fresh: bool = False,
    max_items: int = 8,
) -> tuple[list[dict], str]:
    if not settings.exa_configured or not candidates:
        return [], "direct_notice_skipped"

    client = ExaClient(settings)
    seen_items: set[str] = set()
    unique_candidates: list[DirectRecallNoticeCandidate] = []
    for candidate in candidates:
        item = candidate.item
        if item.id in seen_items:
            continue
        seen_items.add(item.id)
        if len(unique_candidates) >= max_items:
            break
        unique_candidates.append(candidate)

    semaphore = asyncio.Semaphore(3)

    async def lookup(candidate: DirectRecallNoticeCandidate) -> list[dict]:
        item = candidate.item
        async with semaphore:
            return await client.search_direct_recall_notices(
                brand=item.brand,
                product_name=item.product_name,
                upc=item.upc,
                context=" ".join(
                    value
                    for value in [
                        candidate.context,
                        item.supplier_name,
                        item.co_manufacturer_name or "",
                    ]
                    if value
                ),
                days=days,
                force_fresh=force_fresh,
            )

    results: list[dict] = []
    seen_urls: set[str] = set()
    for group in await asyncio.gather(*(lookup(candidate) for candidate in unique_candidates)):
        for result in group:
            url = str(result.get("url") or "")
            if not url or url in seen_urls or is_aggregate_source_url(url):
                continue
            seen_urls.add(url)
            results.append(result)

    if not results:
        return [], "direct_notice_empty"

    urls = [item["url"] for item in results if item.get("url")][:16]
    try:
        content_results = await client.get_contents(urls, force_fresh=force_fresh)
    except Exception:
        return results, "direct_notice_search_only"

    by_url = {item.get("url"): item for item in results if item.get("url")}
    for content in content_results:
        url = content.get("url")
        if url and url in by_url:
            by_url[url].update({key: value for key, value in content.items() if value})
    return list(by_url.values()), "direct_notice_live"


def parse_published_at(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
