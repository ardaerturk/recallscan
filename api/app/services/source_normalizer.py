from hashlib import sha256
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "permalink"}
AGGREGATE_SOURCE_PATHS = {
    ("fda.gov", "/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information"),
    ("fda.gov", "/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements"),
    ("fda.gov", "/safety/recalls-market-withdrawals-safety-alerts"),
    ("fda.gov", "/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls"),
    ("www.fda.gov", "/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information"),
    ("www.fda.gov", "/food/recalls-outbreaks-emergencies/recalls-foods-dietary-supplements"),
    ("www.fda.gov", "/safety/recalls-market-withdrawals-safety-alerts"),
    ("www.fda.gov", "/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls"),
    ("foodsafety.gov", "/recalls-and-outbreaks"),
    ("www.foodsafety.gov", "/recalls-and-outbreaks"),
    ("fsis.usda.gov", "/recalls-alerts"),
    ("www.fsis.usda.gov", "/recalls-alerts"),
}


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or "").lower()
    netloc = hostname
    if parsed.port:
        netloc = f"{hostname}:{parsed.port}"

    kept_params = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        lower = key.lower()
        if lower in TRACKING_PARAMS or any(lower.startswith(prefix) for prefix in TRACKING_PREFIXES):
            continue
        kept_params.append((key, value))

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((parsed.scheme.lower() or "https", netloc, path, "", urlencode(kept_params), ""))


def source_domain(url: str) -> str:
    return urlparse(url).hostname or "unknown"


def is_aggregate_source_url(url: str) -> bool:
    parsed = urlparse(canonicalize_url(url))
    hostname = parsed.hostname or ""
    path = parsed.path.rstrip("/") or "/"
    return (hostname, path) in AGGREGATE_SOURCE_PATHS


def content_hash(title: str, evidence: list[str]) -> str:
    joined = f"{title}\n" + "\n".join(evidence)
    return sha256(" ".join(joined.split()).encode("utf-8")).hexdigest()
