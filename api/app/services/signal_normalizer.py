from datetime import date
from hashlib import sha256
import re
from typing import Any

from api.app.models.domain import NormalizedRecallSignal
from api.app.services.utils import compact, to_date


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _strings(values: Any) -> list[str]:
    output: list[str] = []
    for value in _list(values):
        if isinstance(value, str) and value.strip():
            output.append(value.strip())
        elif isinstance(value, dict):
            for key in ("name", "value", "company", "supplier", "retailer"):
                if isinstance(value.get(key), str) and value[key].strip():
                    output.append(value[key].strip())
                    break
    return sorted(set(output))


def _lot_codes(values: Any) -> list[str]:
    return [value for value in _strings(values) if not _looks_like_date_label(value)]


def _looks_like_date_label(value: str) -> bool:
    text = compact(value)
    return bool(
        re.search(r"\bbest\s+(?:by|before|if\s+used)\b", text)
        or re.search(r"\b(?:use|used|sell)\s+by\b", text)
        or re.search(r"\bexpir(?:ation|es?)\b", text)
    )


def _affected_products(data: dict[str, Any]) -> list[dict[str, Any]]:
    products = data.get("affected_products") or data.get("products") or []
    output: list[dict[str, Any]] = []
    for product in _list(products):
        if isinstance(product, str):
            output.append({"product_name": product})
        elif isinstance(product, dict):
            name = product.get("product_name") or product.get("name") or product.get("product")
            if name or product:
                output.append(
                    {
                        "brand": product.get("brand"),
                        "product_name": name,
                        "size": product.get("size"),
                        "upc": product.get("upc") or product.get("UPC"),
                        "lot_codes": _lot_codes(product.get("lot_codes") or product.get("lots")),
                    }
                )
    return output


def _identifiers(data: dict[str, Any], products: list[dict[str, Any]]) -> dict[str, Any]:
    upcs = _strings(data.get("upcs") or data.get("upc") or data.get("UPCs"))
    lot_codes = _lot_codes(data.get("lot_codes") or data.get("lots"))
    for product in products:
        upcs.extend(_strings(product.get("upc")))
        lot_codes.extend(_lot_codes(product.get("lot_codes")))
    return {
        "upcs": sorted(set(upcs)),
        "lot_codes": sorted(set(lot_codes)),
    }


def _fingerprint(
    company: str | None,
    hazard: str,
    products: list[dict[str, Any]],
    identifiers: dict[str, Any],
    event_date: date | None,
) -> str:
    product_names = sorted(compact(item.get("product_name")) for item in products if item.get("product_name"))
    payload = "|".join(
        [
            compact(company),
            compact(hazard),
            ",".join(product_names),
            ",".join(sorted(compact(upc) for upc in identifiers.get("upcs", []))),
            ",".join(sorted(compact(lot) for lot in identifiers.get("lot_codes", []))),
            event_date.isoformat() if event_date else "",
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def normalize_signal(data: dict[str, Any]) -> NormalizedRecallSignal:
    products = _affected_products(data)
    identifiers = _identifiers(data, products)
    event_date = to_date(data.get("event_date") or data.get("published_date") or data.get("date"))
    company = data.get("company") or data.get("manufacturer") or data.get("brand")
    hazard_type = data.get("hazard_type") or data.get("hazard") or "product_safety"
    hazard_description = data.get("hazard_description") or data.get("description") or hazard_type
    title = data.get("title") or "Product safety signal"
    supplier_chain = []
    for node in _list(data.get("supplier_chain") or data.get("suppliers")):
        if isinstance(node, str):
            supplier_chain.append({"name": node})
        elif isinstance(node, dict):
            supplier_chain.append(node)
    distribution = data.get("distribution") if isinstance(data.get("distribution"), dict) else {}
    if data.get("distribution_states") and "states" not in distribution:
        distribution["states"] = _strings(data.get("distribution_states"))
    explicit_exclusions = []
    for exclusion in _list(data.get("explicit_exclusions") or data.get("exclusions")):
        if isinstance(exclusion, str):
            explicit_exclusions.append({"text": exclusion})
        elif isinstance(exclusion, dict):
            explicit_exclusions.append(exclusion)

    return NormalizedRecallSignal(
        title=title,
        company=company,
        hazard_type=hazard_type,
        hazard_description=hazard_description,
        affected_products=products,
        identifiers=identifiers,
        supplier_chain=supplier_chain,
        retailers=_strings(data.get("retailers")),
        distribution=distribution,
        explicit_exclusions=explicit_exclusions,
        event_date=event_date,
        raw_extraction=data,
        fingerprint=_fingerprint(company, hazard_description, products, identifiers, event_date),
    )
