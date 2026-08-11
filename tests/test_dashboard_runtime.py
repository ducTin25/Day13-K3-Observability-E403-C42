from app.dashboard import calculate


def test_dashboard_calculates_all_six_panels() -> None:
    records = [
        {"event": "request_received", "ts": "2026-08-11T00:00:00Z"},
        {"event": "request_received", "ts": "2026-08-11T03:00:00Z"},
        {"event": "request_received", "ts": "2026-08-11T03:00:01Z"},
        {"event": "request_failed", "ts": "2026-08-11T03:00:02Z", "error_type": "TimeoutError"},
        {"event": "response_sent", "ts": "2026-08-11T03:00:03Z", "latency_ms": 100, "cost_usd": 0.1, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.8},
        {"event": "response_sent", "ts": "2026-08-11T03:00:04Z", "latency_ms": 200, "cost_usd": 0.2, "tokens_in": 30, "tokens_out": 40, "quality_score": 1.0},
    ]

    dashboard = calculate(records)

    assert dashboard["traffic"]["count"] == 2
    assert dashboard["errors"]["error_rate_pct"] == 50.0
    assert dashboard["errors"]["breakdown"] == {"TimeoutError": 1}
    assert dashboard["cost"]["total"] == 0.3
    assert dashboard["tokens"] == {"input": 40, "output": 60}
    assert dashboard["quality"]["mean"] == 0.9
    assert dashboard["latency"]["p95"] == 200.0
