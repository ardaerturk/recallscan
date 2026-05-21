from datetime import date, datetime, timezone
from hashlib import sha256
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:18]}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_date(value: str | date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def normalize_upc(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def compact(value: str | None) -> str:
    return " ".join((value or "").lower().replace("&", " and ").split())


def words(value: str | None) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value or "")
    stop = {"and", "the", "with", "for", "oz", "pack", "single", "brand", "by"}
    return {_word_token(token) for token in cleaned.split() if token and token not in stop}


def _word_token(value: str) -> str:
    synonyms = {
        "beverage": "drink",
        "beverages": "drink",
        "mixes": "mix",
        "products": "product",
    }
    return synonyms.get(value, value)
