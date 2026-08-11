"""JSONL-backed calculations for the six-panel observability dashboard."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any

from .metrics import percentile


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _minute(value: str) -> str:
    return value.replace("Z", "+00:00")[:16]


def _numbers(records: list[dict[str, Any]], event: str, field: str) -> list[float]:
    return [float(record[field]) for record in records if record.get("event") == event and record.get(field) is not None]


def _last_sixty_minutes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dated = [
        (datetime.fromisoformat(record["ts"].replace("Z", "+00:00")), record)
        for record in records
        if record.get("ts")
    ]
    if not dated:
        return []
    latest = max(timestamp for timestamp, _ in dated)
    cutoff = latest - timedelta(minutes=60)
    return [record for timestamp, record in dated if timestamp >= cutoff]


def calculate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return only aggregated values; no request payloads are exposed."""
    records = _last_sixty_minutes(records)
    responses = [record for record in records if record.get("event") == "response_sent"]
    attempts = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [int(value) for value in _numbers(records, "response_sent", "latency_ms")]
    costs = _numbers(records, "response_sent", "cost_usd")
    qualities = _numbers(records, "response_sent", "quality_score")
    traffic_by_minute: dict[str, int] = defaultdict(int)
    cost_by_minute: dict[str, float] = defaultdict(float)
    for record in attempts:
        traffic_by_minute[_minute(record["ts"])] += 1
    for record in responses:
        cost_by_minute[_minute(record["ts"])] += float(record.get("cost_usd", 0))

    error_rate = len(failures) / len(attempts) * 100 if attempts else 0.0
    return {
        "latency": {"p50": percentile(latencies, 50), "p95": percentile(latencies, 95), "p99": percentile(latencies, 99)},
        "traffic": {"count": len(attempts), "by_minute": dict(sorted(traffic_by_minute.items())), "peak_per_minute": max(traffic_by_minute.values(), default=0)},
        "errors": {"error_rate_pct": round(error_rate, 4), "failed_requests": len(failures), "breakdown": dict(Counter(record.get("error_type", "unknown") for record in failures))},
        "cost": {"total": round(sum(costs), 6), "by_minute": {key: round(value, 6) for key, value in sorted(cost_by_minute.items())}},
        "tokens": {"input": int(sum(_numbers(records, "response_sent", "tokens_in"))), "output": int(sum(_numbers(records, "response_sent", "tokens_out")))},
        "quality": {"mean": round(mean(qualities), 4) if qualities else 0.0},
    }
