from api.app.services.exa_client import successful_content_results


def test_successful_content_results_skips_failed_url_statuses():
    data = {
        "results": [
            {"id": "req_1", "url": "https://example.com/ok", "text": "ok"},
            {"id": "req_2", "url": "https://example.com/missing", "text": "missing"},
            {"id": "req_3", "url": "https://example.com/error", "text": "error"},
        ],
        "statuses": [
            {"id": "req_1", "status": "success"},
            {"id": "req_2", "status": "error", "error": {"httpStatusCode": 404}},
        ],
    }
    data["results"][2]["statusCode"] = 500

    assert successful_content_results(data) == [{"id": "req_1", "url": "https://example.com/ok", "text": "ok"}]


def test_successful_content_results_keeps_results_without_status_code():
    data = {"results": [{"url": "https://example.com/ok", "text": "ok"}]}
    assert successful_content_results(data) == [{"url": "https://example.com/ok", "text": "ok"}]
