from api.app.models.db import ExposureMatch, RecallSignal


def recommended_action(tier: str) -> str:
    return {
        "confirmed_match": "Pull matched SKU or lot.",
        "supplier_review": "Confirm ingredient-lot exposure with supplier.",
        "watch_only": "Monitor for product, UPC, lot, or supplier confirmation.",
        "no_exposure": "Log the exclusion.",
    }.get(tier, "Review evidence before taking inventory action.")


def build_action_memo(signal: RecallSignal, matches: list[ExposureMatch]) -> str:
    if not matches:
        return "No catalog exposure found. Keep the source in the watch log and rescan if the announcement is updated."

    by_tier = {match.tier for match in matches}
    if "confirmed_match" in by_tier:
        action = "Confirmed exposure exists. Start a SKU and lot pull for the affected inventory, then contact the supplier for root-cause and replacement timing."
    elif "supplier_review" in by_tier:
        action = "Supplier-chain exposure is plausible. Open a supplier review and ask for ingredient-lot traceability before pulling product."
    elif "watch_only" in by_tier:
        action = "The signal is nearby but weak. Keep it on watch and wait for a product, UPC, lot, or supplier confirmation."
    else:
        action = "The source explicitly excludes the matched catalog item or product family. Log the exclusion."

    evidence_count = len(signal.raw_extraction_json.get("evidence", []))
    return f"{action} Evidence attached: {evidence_count} source excerpt{'s' if evidence_count != 1 else ''}."
