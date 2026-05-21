from api.app.services.source_classification import (
    classify_source,
    is_action_source_type,
    is_direct_recall_notice_result,
    looks_like_direct_recall_notice_title,
)


def test_fda_recall_notice_is_action_source():
    source_type = classify_source(
        "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/example-company-recalls-product",
        "Example Company Recalls Product Because of Possible Health Risk",
    )
    assert source_type == "official_recall"
    assert is_action_source_type(source_type)


def test_direct_company_recall_title_is_action_source():
    source_type = classify_source(
        "https://examplemanufacturer.com/news/example-company-issues-recall",
        "Example Company Issues Voluntary Recall of Grocery Product Due to Undeclared Milk",
    )
    assert source_type == "direct_recall_notice"
    assert is_action_source_type(source_type)


def test_press_release_recall_title_is_direct_notice():
    assert looks_like_direct_recall_notice_title(
        "GHIRARDELLI CHOCOLATE COMPANY RECALLS POWDERED BEVERAGE MIXES BECAUSE OF POSSIBLE HEALTH RISK"
    )


def test_recall_news_roundup_is_not_direct_notice():
    title = "Kroger Croutons Recalled Over Salmonella Risk"
    assert not looks_like_direct_recall_notice_title(title)
    assert not is_direct_recall_notice_result("https://example-news.com/kroger-croutons-recalled", title)


def test_consumer_news_recall_title_is_not_direct_notice():
    assert not looks_like_direct_recall_notice_title("Ghirardelli Announces Recall on 13 Products—Here's What to Know")
    assert not looks_like_direct_recall_notice_title(
        "Ghirardelli recalls powdered drink mixes for potential salmonella contamination"
    )


def test_cdc_study_is_monitoring_source():
    assert classify_source("https://www.cdc.gov/mmwr/volumes/75/wr/mm7513a2.htm", "MMWR Study") == "outbreak_update"
