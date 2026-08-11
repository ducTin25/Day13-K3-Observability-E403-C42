import pytest

from app import metrics


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


@pytest.fixture(autouse=True)
def clear_metrics() -> None:
    metrics.reset()
    yield
    metrics.reset()


def test_error_rate_is_zero_without_attempts() -> None:
    snapshot = metrics.snapshot()

    assert snapshot["total_request_attempts"] == 0
    assert snapshot["failed_requests"] == 0
    assert snapshot["error_rate_pct"] == 0.0


def test_error_rate_is_zero_for_successful_attempts() -> None:
    metrics.record_request_attempt()
    metrics.record_request_attempt()

    snapshot = metrics.snapshot()

    assert snapshot["traffic"] == 2
    assert snapshot["error_rate_pct"] == 0.0


def test_error_rate_and_breakdown_count_each_failed_request_once() -> None:
    for _ in range(4):
        metrics.record_request_attempt()
    metrics.record_error("TimeoutError", "request-1")
    metrics.record_error("TimeoutError", "request-1")
    metrics.record_error("ValueError", "request-2")

    snapshot = metrics.snapshot()

    assert snapshot["failed_requests"] == 2
    assert snapshot["error_rate_pct"] == 50.0
    assert snapshot["error_breakdown"] == {"TimeoutError": 1, "ValueError": 1}


def test_error_rate_cannot_exceed_one_hundred_percent_for_duplicate_request_ids() -> None:
    metrics.record_request_attempt()
    metrics.record_error("RuntimeError", "request-1")
    metrics.record_error("ValueError", "request-1")

    assert metrics.snapshot()["error_rate_pct"] == 100.0
