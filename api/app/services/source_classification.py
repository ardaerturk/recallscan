import re
from urllib.parse import urlparse

from api.app.services.source_normalizer import is_aggregate_source_url


ACTION_SOURCE_TYPES = {"official_recall", "public_health_alert", "direct_recall_notice"}

_DIRECT_NOTICE_PATTERNS = [
    re.compile(
        r"\b(?:issues?|announces?|initiates?|expands?)\s+(?:a\s+)?(?:voluntary\s+)?recall\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bvoluntarily\s+recalls?\b", re.IGNORECASE),
    re.compile(
        r"\brecalls?\s+.{3,160}\b("
        r"because of possible health risk|due to possible health risk|because of possible|due to possible|"
        r"undeclared|allergy alert"
        r")\b",
        re.IGNORECASE,
    ),
]

_NON_NOTICE_TITLE_PATTERN = re.compile(
    r"\b("
    r"what to check|how to check|what to know|what you should know|here'?s what|list of|roundup|study|investigation|mmwr|"
    r"linked to|tied to|brand-by-brand|fallout|cascade|sparks|"
    r"recalled over|recalled after|fda warns|fda recalls|cdc|recall alert|popular|sold locally"
    r")\b",
    re.IGNORECASE,
)


def classify_source(url: str, title: str = "") -> str:
    lowered = url.lower()
    if _is_fda_recall_notice_url(lowered):
        return "official_recall"
    if _is_fsis_recall_notice_url(lowered):
        return "public_health_alert"
    if "fda.gov/food/outbreaks-foodborne-illness/" in lowered:
        return "outbreak_update"
    if "cdc.gov" in lowered:
        return "outbreak_update"
    if looks_like_direct_recall_notice_title(title):
        return "direct_recall_notice"
    return "external_signal"


def is_action_source_type(source_type: str) -> bool:
    return source_type in ACTION_SOURCE_TYPES


def is_direct_recall_notice_result(url: str, title: str = "") -> bool:
    if not url or is_aggregate_source_url(url):
        return False
    lowered = url.lower()
    return (
        _is_fda_recall_notice_url(lowered)
        or _is_fsis_recall_notice_url(lowered)
        or looks_like_direct_recall_notice_title(title)
    )


def looks_like_direct_recall_notice_title(title: str) -> bool:
    value = " ".join((title or "").split())
    if not value or _NON_NOTICE_TITLE_PATTERN.search(value):
        return False
    if re.match(r"^company\s+issues?\b", value, flags=re.IGNORECASE):
        return False
    if len(value) > 220:
        value = value[:220]
    return any(pattern.search(value) for pattern in _DIRECT_NOTICE_PATTERNS)


def _is_fda_recall_notice_url(lowered_url: str) -> bool:
    if "fda.gov/safety/recalls-market-withdrawals-safety-alerts/" not in lowered_url:
        return False
    return not is_aggregate_source_url(lowered_url)


def _is_fsis_recall_notice_url(lowered_url: str) -> bool:
    if "fsis.usda.gov/recalls-alerts/" not in lowered_url:
        return False
    path = urlparse(lowered_url).path.rstrip("/")
    return path != "/recalls-alerts"
