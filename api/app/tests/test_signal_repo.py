from api.app.models.db import ExternalSource
from api.app.repositories.signal_repo import _source_priority


def source(source_type: str) -> ExternalSource:
    return ExternalSource(
        id=f"src_{source_type}",
        canonical_url=f"https://example.com/{source_type}",
        source_domain="example.com",
        source_type=source_type,
        title=source_type,
        raw_exa_result_json={},
    )


def test_official_recall_source_has_priority_over_direct_notice() -> None:
    assert _source_priority(source("official_recall")) < _source_priority(source("direct_recall_notice"))


def test_public_health_alert_source_has_priority_over_external_signal() -> None:
    assert _source_priority(source("public_health_alert")) < _source_priority(source("external_signal"))
