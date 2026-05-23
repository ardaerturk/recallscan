import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from api.app.config import Settings
from api.app.services.source_classification import is_direct_recall_notice_result


RECALL_SUMMARY_QUERY = (
    "Extract factual food recall intelligence for a grocery recall manager. Return only facts stated "
    "by the source: affected product objects with brand and product name, UPCs, lot codes, hazard, "
    "distribution, explicit exclusions, and supplier-chain company objects with roles. Use product names, "
    "not article headlines. Leave unknown fields empty."
)

RECALL_CONTENT_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Food Recall Signal",
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short recall title using the affected product, not the article headline."},
        "company": {"type": "string", "description": "Company, manufacturer, or recall sponsor named by the source."},
        "hazard_type": {"type": "string", "description": "Hazard such as salmonella, listeria, undeclared allergen, or foreign material."},
        "affected_products": {
            "type": "array",
            "description": "Products explicitly named as recalled or affected.",
            "items": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string", "description": "Brand printed on the affected product, if stated."},
                    "product_name": {"type": "string", "description": "Specific affected product name, not a broad category."},
                    "size": {"type": "string", "description": "Package size, if stated."},
                    "upc": {"type": "string", "description": "UPC or barcode, if stated."},
                    "lot_codes": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "upcs": {"type": "array", "items": {"type": "string"}},
        "lot_codes": {"type": "array", "items": {"type": "string"}},
        "supplier_chain": {
            "type": "array",
            "description": "Companies in the upstream or downstream chain. Return company names only.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Company name only."},
                    "role": {"type": "string", "description": "Role such as ingredient supplier, processor, manufacturer, retailer."},
                },
            },
        },
        "retailers": {"type": "array", "items": {"type": "string"}},
        "distribution_states": {"type": "array", "items": {"type": "string"}},
        "explicit_exclusions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Explicit statement that a product, lot, flavor, or family is not affected."},
                },
            },
        },
    },
}

SUPPLIER_LOOKUP_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Food Supplier Contact",
    "type": "object",
    "properties": {
        "company_name": {"type": "string", "description": "Supplier company name."},
        "website": {"type": "string", "description": "Official website URL if found."},
        "phone": {"type": "string", "description": "Main phone number, customer service number, or corporate contact phone if found."},
        "email": {"type": "string", "description": "Public contact email if found."},
        "address": {"type": "string", "description": "Public headquarters or mailing address if found."},
        "recall_or_quality_contact": {"type": "string", "description": "Recall, quality, food safety, or customer care contact detail if found."},
        "logo_url": {"type": "string", "description": "Logo or favicon URL from an official source if found."},
        "notes": {"type": "string", "description": "One short factual note about what the supplier does or how it relates to the product."},
    },
}

PRODUCT_ASSET_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Catalog Product Asset",
    "type": "object",
    "properties": {
        "product_name": {
            "type": "string",
            "description": "The catalog product represented by the page.",
        },
        "page_url": {
            "type": "string",
            "description": "The official brand, retailer, or grocery product page used for the asset.",
        },
        "image_url": {
            "type": "string",
            "description": (
                "A direct product package or product photo URL. Leave empty for logos, favicons, "
                "government recall pages, news images, social images, or generic illustrations."
            ),
        },
        "source_domain": {
            "type": "string",
            "description": "Domain of the product page.",
        },
    },
}

RECALL_AUTHORITY_DOMAINS = {"fda.gov", "cdc.gov", "fsis.usda.gov", "foodsafety.gov"}


class ExaClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.exa_api_key:
            raise RuntimeError("EXA_API_KEY is required to run Exa scans.")
        self._api_key = settings.exa_api_key
        self._base_url = "https://api.exa.ai"

    async def search_recent_recalls(self, *, days: int, force_fresh: bool = False) -> list[dict[str, Any]]:
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        official, supplier = await asyncio.gather(
            self._search(
                query=(
                    "Recent food recall or public health alert. Extract affected products, brands, UPCs, "
                    "lot codes, hazards, allergens, suppliers, retailers, distribution states, "
                    "and explicit statements about products not affected."
                ),
                include_domains=["fda.gov", "foodsafety.gov", "fsis.usda.gov", "cdc.gov"],
                start_published_date=start_date,
                num_results=40,
                search_type="auto",
                max_age_hours=0 if force_fresh else 24,
            ),
            self._search(
                query=(
                    "Recent food recall caused by upstream ingredient contamination, supplier recall, "
                    "co-manufacturer cross-contact, seasoning blend, powdered milk, allergens, or shared equipment."
                ),
                include_domains=None,
                start_published_date=start_date,
                num_results=30,
                search_type="deep-lite",
                max_age_hours=0 if force_fresh else 24,
            ),
        )
        return _dedupe_results([*official, *supplier])

    async def search_direct_recall_notices(
        self,
        *,
        brand: str,
        product_name: str,
        upc: str | None = None,
        context: str = "",
        days: int,
        force_fresh: bool = False,
    ) -> list[dict[str, Any]]:
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        queries = _recall_notice_queries(
            brand=brand,
            product_name=product_name,
            upc=upc,
            context=context,
        )
        result_groups = await asyncio.gather(
            *(
                self._search(
                    query=query,
                    include_domains=["fda.gov", "fsis.usda.gov"],
                    start_published_date=start_date,
                    num_results=12,
                    search_type="auto",
                    max_age_hours=0 if force_fresh else 24,
                )
                for query in queries
            )
        )
        results = [result for group in result_groups for result in group]
        return [
            result
            for result in _dedupe_results(results)
            if is_direct_recall_notice_result(
                str(result.get("url") or ""),
                str(result.get("title") or ""),
            )
        ]

    async def get_contents(self, urls: list[str], *, force_fresh: bool = False) -> list[dict[str, Any]]:
        if not urls:
            return []
        payload = {
            "urls": urls,
            "highlights": {
                "query": (
                    "affected food products, UPCs, lot codes, hazards, supplier chain, "
                    "retail distribution, and explicit exclusions"
                )
            },
            "summary": {
                "query": RECALL_SUMMARY_QUERY,
                "schema": RECALL_CONTENT_SCHEMA,
            },
            "extras": {"imageLinks": 3},
            "maxAgeHours": 0 if force_fresh else 24,
            "livecrawlTimeout": 12000,
        }
        data = await self._post("/contents", payload, result_key=None)
        return successful_content_results(data)

    async def lookup_supplier(self, supplier_name: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": (
                f"{supplier_name} food supplier official website contact phone quality assurance recall"
            ),
            "type": "auto",
            "numResults": 5,
            "contents": {
                "highlights": {
                    "query": "official website, contact, phone, email, headquarters, customer care, quality assurance, recall contact",
                    "maxCharacters": 1200,
                },
                "maxAgeHours": 24,
            },
            "systemPrompt": (
                "Find official or high-quality public pages about the supplier. Return only facts grounded in the results. "
                "Leave fields empty when contact details are not available."
            ),
            "outputSchema": SUPPLIER_LOOKUP_SCHEMA,
        }
        data = await self._post("/search", payload, result_key=None)
        return {
            "query": supplier_name,
            "details": _parse_output_content(data),
            "sources": [
                {
                    "title": result.get("title") or result.get("url"),
                    "url": result.get("url"),
                    "domain": _domain(result.get("url", "")),
                    "image_url": result.get("image"),
                    "favicon_url": result.get("favicon"),
                    "highlights": result.get("highlights") or [],
                }
                for result in data.get("results", [])[:5]
                if result.get("url")
            ],
        }

    async def lookup_product_asset(
        self,
        *,
        brand: str,
        product_name: str,
        upc: str | None = None,
        category: str | None = None,
    ) -> dict[str, str]:
        query_parts = [
            upc or "",
            f'"{brand}"',
            f'"{product_name}"',
            category or "",
            "official product page package photo grocery product image",
        ]
        payload: dict[str, Any] = {
            "query": " ".join(part for part in query_parts if part).strip(),
            "type": "auto",
            "numResults": 8,
            "excludeDomains": sorted(RECALL_AUTHORITY_DOMAINS),
            "contents": {
                "highlights": {
                    "query": "product name, brand, package photo, product image, UPC, grocery item",
                    "maxCharacters": 900,
                },
                "extras": {"imageLinks": 6},
                "maxAgeHours": 168,
            },
            "systemPrompt": (
                "Find a public product page for the catalog item. Prefer official brand pages and retailer product "
                "pages. Avoid recall notices, government pages, news articles, logos, favicons, social images, and "
                "generic illustrations. Return empty strings when no product photo is grounded in the results."
            ),
            "outputSchema": PRODUCT_ASSET_SCHEMA,
        }
        data = await self._post("/search", payload, result_key=None)
        for candidate in _product_asset_candidates_from_search(data):
            if await _image_url_available(candidate["product_image_url"]):
                return candidate
        return {}

    async def _search(
        self,
        *,
        query: str,
        include_domains: list[str] | None,
        start_published_date: str,
        num_results: int,
        search_type: str,
        max_age_hours: int,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "query": query,
            "type": search_type,
            "numResults": num_results,
            "startPublishedDate": start_published_date,
            "contents": {
                "highlights": {
                    "query": (
                        "affected food products, UPCs, lot codes, hazards, supplier chain, "
                        "retail distribution, and explicit exclusions"
                    ),
                },
                "extras": {"imageLinks": 3},
                "maxAgeHours": max_age_hours,
            },
        }
        if include_domains:
            payload["includeDomains"] = include_domains

        data = await self._post("/search", payload, result_key=None)
        results = data.get("results", [])
        return attach_structured_candidates(data, results)

    async def _post(self, path: str, payload: dict[str, Any], result_key: str | None):
        headers = {"x-api-key": self._api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(base_url=self._base_url, timeout=35) as client:
            response = await client.post(path, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get(result_key, []) if result_key else data


def _dedupe_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output = []
    for result in results:
        url = result.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        output.append(result)
    return output


def successful_content_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    results = data.get("results")
    if not isinstance(results, list):
        return []

    statuses_by_id = _content_statuses_by_id(data.get("statuses"))
    output: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        status = statuses_by_id.get(str(result.get("id") or "")) or statuses_by_id.get(str(result.get("url") or ""))
        if _content_result_failed(result, status):
            continue
        output.append(result)
    return output


def _content_statuses_by_id(statuses: object) -> dict[str, dict[str, Any]]:
    if not isinstance(statuses, list):
        return {}
    output: dict[str, dict[str, Any]] = {}
    for status in statuses:
        if not isinstance(status, dict):
            continue
        key = str(status.get("id") or status.get("url") or "")
        if key:
            output[key] = status
    return output


def _content_result_failed(result: dict[str, Any], status: dict[str, Any] | None) -> bool:
    status_value = str((status or {}).get("status") or "").lower()
    if status_value == "error":
        return True
    status_code = _status_code(result.get("statusCode") or result.get("status_code"))
    if status_code is None and status:
        error = status.get("error")
        status_code = _status_code((error or {}).get("httpStatusCode") if isinstance(error, dict) else None)
    return status_code is not None and status_code >= 400


def _status_code(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _recall_notice_queries(*, brand: str, product_name: str, upc: str | None, context: str) -> list[str]:
    context_short = _short_query_context(context)
    products = _text_variants(product_name)
    queries: list[str] = []
    for product in products:
        queries.append(
            " ".join(
                part
                for part in [
                    f'"{brand}"',
                    f'"{product}"',
                    upc or "",
                    "official recall notice manufacturer announcement FDA FSIS",
                ]
                if part
            )
        )
        queries.append(
            " ".join(
                part
                for part in [
                    context_short,
                    f'"{brand}"',
                    f'"{product}"',
                    upc or "",
                    "recall notice safety alert",
                ]
                if part
            )
        )
        queries.append(
            " ".join(
                part
                for part in [
                    context_short,
                    brand,
                    product,
                    "because of possible health risk recall",
                ]
                if part
            )
        )
    return list(dict.fromkeys(queries[:2]))


def _text_variants(value: str) -> list[str]:
    variants = [value]
    stripped = _strip_package_size(value)
    if stripped != value:
        variants.append(stripped)
    beverage_variant = _replace_word(value, "drink", "beverage")
    if beverage_variant != value:
        variants.append(beverage_variant)
    stripped_beverage_variant = _replace_word(stripped, "drink", "beverage")
    if stripped_beverage_variant not in variants:
        variants.append(stripped_beverage_variant)
    return variants


def _short_query_context(value: str) -> str:
    words = value.split()
    return " ".join(words[:18])


def _replace_word(value: str, old: str, new: str) -> str:
    import re

    return re.sub(rf"\b{re.escape(old)}\b", new, value, flags=re.IGNORECASE)


def _strip_package_size(value: str) -> str:
    import re

    text = re.sub(
        r"\b\d+(?:\.\d+)?\s?(?:oz|ounce|ounces|lb|lbs|g|kg|ml|ct|count|pack|bags?)\b",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return " ".join(text.split()).strip()


def _parse_output_content(data: dict[str, Any]) -> dict[str, Any]:
    output = data.get("output")
    if not isinstance(output, dict):
        return {}
    content = output.get("content")
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            import json

            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except ValueError:
            return {}
    return {}


def _domain(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.replace("www.", "")


def _product_asset_from_search(data: dict[str, Any]) -> dict[str, str]:
    return next(iter(_product_asset_candidates_from_search(data)), {})


def _product_asset_candidates_from_search(data: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    output = _parse_output_content(data)
    page_url = str(output.get("page_url") or "").strip()
    image_url = str(output.get("image_url") or "").strip()
    source_domain = str(output.get("source_domain") or _domain(page_url)).strip()
    if _valid_product_asset_source(page_url) and _valid_product_image_url(image_url):
        candidates.append(
            {
                "product_image_url": image_url,
                "product_image_source_url": page_url,
                "product_image_source_domain": source_domain or _domain(page_url),
            }
        )

    for result in data.get("results", []):
        if not isinstance(result, dict) or not _valid_product_asset_source(str(result.get("url") or "")):
            continue
        source_url = str(result.get("url") or "")
        for candidate in _result_image_candidates(result):
            if _valid_product_image_url(candidate):
                candidates.append(
                    {
                        "product_image_url": candidate,
                        "product_image_source_url": source_url,
                        "product_image_source_domain": _domain(source_url),
                    }
                )
    return _dedupe_asset_candidates(candidates)


def _dedupe_asset_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output = []
    for candidate in candidates:
        url = candidate["product_image_url"]
        if url in seen:
            continue
        seen.add(url)
        output.append(candidate)
    return output


async def _image_url_available(url: str) -> bool:
    headers = {"Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"}
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
            response = await client.get(url, headers={"Range": "bytes=0-1023"})
            if response.status_code not in {200, 206}:
                response = await client.get(url)
    except httpx.HTTPError:
        return False
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    return response.status_code in {200, 206} and content_type.startswith("image/")


def _result_image_candidates(result: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    if isinstance(result.get("image"), str):
        candidates.append(result["image"])
    extras = result.get("extras")
    if isinstance(extras, dict) and isinstance(extras.get("imageLinks"), list):
        candidates.extend(value for value in extras["imageLinks"] if isinstance(value, str))
    return candidates


def _valid_product_asset_source(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    domain = _domain(url).lower()
    if _is_recall_authority_domain(domain):
        return False
    lowered = url.lower()
    return not any(token in lowered for token in ("/recall", "recall-", "recalls", "outbreak", "safety-alert"))


def _valid_product_image_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    lowered = url.lower().split("?", 1)[0]
    if _is_recall_authority_domain(_domain(url).lower()):
        return False
    blocked_image_tokens = (
        "favicon",
        "apple-touch-icon",
        "logo",
        "icon",
        "sprite",
        "placeholder",
        "default",
        "seal",
    )
    if any(token in lowered for token in blocked_image_tokens):
        return False
    return lowered.endswith((".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"))


def _is_recall_authority_domain(domain: str) -> bool:
    return any(domain == authority or domain.endswith(f".{authority}") for authority in RECALL_AUTHORITY_DOMAINS)


def attach_structured_candidates(data: dict[str, Any], results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for candidate in _output_candidates(data):
        matched = _match_candidate_to_result(candidate, results)
        if matched is not None:
            matched["structured"] = candidate
    return results


def _output_candidates(data: dict[str, Any]) -> list[dict[str, Any]]:
    output = data.get("output")
    if not isinstance(output, dict):
        return []
    content = output.get("content")
    if isinstance(content, str):
        try:
            import json

            content = json.loads(content)
        except ValueError:
            return []
    if not isinstance(content, dict):
        return []
    if isinstance(content.get("recall_candidates"), list):
        return [item for item in content["recall_candidates"] if isinstance(item, dict)]
    if content.get("title") and content.get("hazard_type"):
        return [content]
    return []


def _match_candidate_to_result(candidate: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any] | None:
    source_url = (candidate.get("source_url") or "").strip()
    if source_url:
        for result in results:
            if result.get("url") == source_url:
                return result
    candidate_title = (candidate.get("title") or "").lower().strip()
    if not candidate_title:
        return None
    for result in results:
        title = (result.get("title") or "").lower()
        if candidate_title[:40] and candidate_title[:40] in title:
            return result
    return None
