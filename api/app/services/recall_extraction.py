import json
import re
from typing import Any

HAZARD_WORDS = {
    "salmonella": "potential_salmonella",
    "listeria": "potential_listeria",
    "e. coli": "potential_ecoli",
    "ecoli": "potential_ecoli",
    "peanut": "undeclared_allergen",
    "milk": "undeclared_allergen",
    "soy": "undeclared_allergen",
    "sesame": "undeclared_allergen",
    "foreign material": "foreign_material",
}


def infer_hazard(text: str) -> tuple[str, str]:
    lower = text.lower()
    for needle, hazard in HAZARD_WORDS.items():
        if needle in lower:
            return hazard, needle.title() if hazard.startswith("potential") else f"Possible {needle} exposure"
    if "allergen" in lower or "undeclared" in lower:
        return "undeclared_allergen", "Possible undeclared allergen"
    if "recall" in lower:
        return "recall_notice", "Recall notice"
    return "product_safety", "Product safety signal"


def extract_from_exa_result(result: dict[str, Any]) -> dict[str, Any]:
    title = result.get("title") or result.get("url") or "Product safety signal"
    text_parts = [title]
    evidence_parts: list[str] = []
    for highlight in result.get("highlights") or []:
        if isinstance(highlight, str):
            text_parts.append(highlight)
            evidence_parts.append(highlight)
        elif isinstance(highlight, dict):
            text = str(highlight.get("text") or highlight.get("highlight") or "")
            text_parts.append(text)
            if text:
                evidence_parts.append(text)
    if result.get("summary"):
        text_parts.append(str(result["summary"]))
        if not _looks_like_structured_json(result["summary"]):
            evidence_parts.append(str(result["summary"]))
    text = "\n".join(part for part in text_parts if part)
    hazard_type, hazard_description = infer_hazard(text)
    data = _structured_payload(result)
    supplier_chain = data.get("supplier_chain") or _supplier_chain_guess(text)
    merged = {
        "title": data.get("title") or title,
        "company": data.get("company"),
        "hazard_type": data.get("hazard_type") or hazard_type,
        "hazard_description": data.get("hazard_description") or hazard_description,
        "affected_products": data.get("affected_products") or _product_guess(title),
        "upcs": data.get("upcs", []),
        "lot_codes": data.get("lot_codes", []),
        "supplier_chain": supplier_chain,
        "affected_materials": data.get("affected_materials", []),
        "retailers": data.get("retailers", []),
        "distribution": data.get("distribution")
        or {
            "states": data.get("distribution_states", []),
            "channels": data.get("distribution_channels", []),
        },
        "explicit_exclusions": data.get("explicit_exclusions", []),
        "event_date": result.get("publishedDate") or data.get("event_date"),
        "evidence": [line for line in evidence_parts if line],
        "source_url": result.get("url"),
    }
    return merged


def _structured_payload(result: dict[str, Any]) -> dict[str, Any]:
    summary = result.get("summary")
    if isinstance(summary, dict):
        return {**_search_structured_payload(result), **summary}
    if isinstance(summary, str):
        try:
            parsed = json.loads(summary)
            if isinstance(parsed, dict):
                return {**_search_structured_payload(result), **parsed}
        except ValueError:
            pass
    return _search_structured_payload(result)


def _search_structured_payload(result: dict[str, Any]) -> dict[str, Any]:
    structured = result.get("structured")
    return structured if isinstance(structured, dict) else {}


def _looks_like_structured_json(value: object) -> bool:
    if isinstance(value, dict):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    return text.startswith("{") or text.startswith("[")


def _product_guess(title: str) -> list[dict[str, Any]]:
    product_name = _clean_product_from_title(title)
    return [{"product_name": product_name}] if product_name else []


def _clean_product_from_title(title: str) -> str:
    value = title.split("|")[0].strip()
    recall_announcement = re.match(
        r"^(.+?)\s+"
        r"(?:issues?|announces?|initiates?|expands?)\s+"
        r"(?:a\s+)?(?:voluntary\s+)?recall\s+"
        r"(?:of|for)?\s+"
        r"(.+?)(?:\s+over\b|\s+due\b|\s+because\b|,|:|\s+[–—-]\s+|$)",
        value,
        flags=re.IGNORECASE,
    )
    if recall_announcement:
        return _clean_product_candidate(_strip_scope_prefix(recall_announcement.group(2)))

    voluntary_recall = re.match(
        r"^(.+?)\s+voluntarily\s+recalls?\s+(.+?)(?:\s+over\b|\s+due\b|\s+because\b|,|:|\s+[–—-]\s+|$)",
        value,
        flags=re.IGNORECASE,
    )
    if voluntary_recall:
        return _clean_product_candidate(_strip_scope_prefix(voluntary_recall.group(2)))

    recalls = re.match(
        r"^(.+?)\s+recalls?\s+(.+?)(?:\s+over\b|\s+due\b|\s+because\b|,|:|\s+[–—-]\s+|$)",
        value,
        flags=re.IGNORECASE,
    )
    if recalls and not _starts_with_news_verb(recalls.group(2)):
        return _clean_product_candidate(f"{recalls.group(1)} {recalls.group(2)}")

    recall_index = re.search(r"\brecall(?:s|ed|ing)?\b", value, flags=re.IGNORECASE)
    if recall_index and recall_index.start() > 0:
        return _clean_product_candidate(value[: recall_index.start()].rstrip(":-–— "))

    return _clean_product_candidate(value.split(":")[0].strip())


def _clean_product_candidate(value: str) -> str:
    text = _strip_size(value.split("|")[0])
    text = re.sub(r"^(fds issue|fda warns?|usda|cdc)\s+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^\s*the\s+", "", text, flags=re.IGNORECASE).strip()
    after = re.match(r"what to check after\s+(?:the\s+)?(.+)$", text, flags=re.IGNORECASE)
    if after:
        return _clean_product_candidate(after.group(1))
    risk_from = re.search(r"\brisk from\s+(.+?)(?:[:\-–—]|$)", text, flags=re.IGNORECASE)
    if risk_from:
        return _clean_product_candidate(risk_from.group(1))
    text = re.sub(r"\s+(?:linked\s+to|tied\s+to)\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s+(?:sparks?|fears?|warning|warns?|after|across|about|over|due\s+to|because)\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+(?:cascade|fallout)\b.*$", "", text, flags=re.IGNORECASE)
    return " ".join(text.split()).strip()


def _strip_scope_prefix(value: str) -> str:
    return re.sub(
        r"^(?:specific\s+)?(?:affected\s+)?(?:lots?\s+of|batches?\s+of|packages?\s+of)\s+",
        "",
        value.strip(),
        flags=re.IGNORECASE,
    )


def _starts_with_news_verb(value: str) -> bool:
    return bool(
        re.match(
            r"(and|sparks?|fears?|warning|warns?|after|across|about|linked\s+to|tied\s+to|over|due\s+to|because|cascade|fallout)\b",
            value.strip(),
            flags=re.IGNORECASE,
        )
    )


def _strip_size(value: str) -> str:
    text = re.sub(
        r"\b\d+(?:\.\d+)?\s?(?:oz|ounce|ounces|lb|lbs|g|kg|ml|ct|count|pack|bags?)\b",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return " ".join(text.split()).strip()


def _supplier_chain_guess(text: str) -> list[dict[str, str]]:
    """Extract supplier-chain names from recall prose when Exa summary is not structured."""
    nodes: list[dict[str, str]] = []

    supplied = re.search(
        r"supplied by\s+(.+?)\s+to\s+(.+?)(?:,|\s+which|\s+and|\.)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if supplied:
        nodes.extend(
            [
                {"name": _clean_company_name(supplied.group(1)), "role": "ingredient supplier"},
                {"name": _clean_company_name(supplied.group(2)), "role": "processor"},
            ]
        )

    sold_to = re.search(
        r"(?:sold to|sells? to)\s+(.+?)(?:\s+and|\s+which|,|\.)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if sold_to:
        nodes.append({"name": _clean_company_name(sold_to.group(1)), "role": "downstream manufacturer"})

    manufacturer = re.search(
        r"manufacturer\s+(.+?)\s+(?:confirmed|said|announced|recalled)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if manufacturer:
        nodes.append({"name": _clean_company_name(manufacturer.group(1)), "role": "manufacturer"})

    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for node in nodes:
        name = node["name"]
        key = re.sub(
            r"\b(llc|inc|incorporated|corp|corporation|co|company)\b",
            "",
            name.lower().replace(".", ""),
        )
        key = " ".join(key.split())
        if not _valid_company_name(name) or key in seen:
            continue
        seen.add(key)
        output.append(node)
    return output


def _clean_company_name(value: str) -> str:
    text = " ".join(value.replace("\n", " ").split())
    comma_parts = [part.strip() for part in text.split(",") if part.strip()]
    if (
        len(comma_parts) > 1
        and len(comma_parts[-1].split()) >= 2
        and re.search(r"\b(inc|llc|ltd|corp|corporation|company|co|usa|foods)\b", comma_parts[-1], re.IGNORECASE)
    ):
        text = comma_parts[-1]
    text = re.sub(r"^(the|a|an)\s+", "", text, flags=re.IGNORECASE)
    text = re.split(r"\s+(?:for|used|that|with|after|before)\s+", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = text.strip(" ,.;:'\"“”()[]")
    return text[:80]


def _valid_company_name(value: str) -> bool:
    words = value.split()
    if value.lower() in {"and", "or", "nor", "the", "of", "for", "from", "by", "to", "in", "on", "with", "use"}:
        return False
    if len(value) < 3 or len(value) > 80:
        return False
    if re.match(r"^(of|for|from|by|to|in|on|with)\s+", value, flags=re.IGNORECASE):
        return False
    if ";" in value or ":" in value:
        return False
    if re.search(
        r"\b(the recalls|announced by|health officials|recall notice|according to|however|consumer|use)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return False
    if len(words) > 9 and not re.search(
        r"\b(inc|llc|ltd|corp|corporation|company|co|usa|foods|dairies)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return False
    return True
