from __future__ import annotations

from collections import Counter
from statistics import mean

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
REQUEST_ATTEMPTS: int = 0
FAILED_REQUESTS: int = 0
FAILED_REQUEST_IDS: set[str] = set()
QUALITY_SCORES: list[float] = []


def record_request_attempt() -> None:
    """Record one /chat request that reached the application handler."""
    global REQUEST_ATTEMPTS
    REQUEST_ATTEMPTS += 1


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)



def record_error(error_type: str, request_id: str | None = None) -> None:
    """Record a failed request once, while retaining its error-type breakdown."""
    global FAILED_REQUESTS
    if request_id is not None:
        if request_id in FAILED_REQUEST_IDS:
            return
        FAILED_REQUEST_IDS.add(request_id)
    FAILED_REQUESTS += 1
    ERRORS[error_type] += 1



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    error_rate_pct = (FAILED_REQUESTS / REQUEST_ATTEMPTS * 100) if REQUEST_ATTEMPTS else 0.0
    return {
        "traffic": REQUEST_ATTEMPTS,
        "total_request_attempts": REQUEST_ATTEMPTS,
        "failed_requests": FAILED_REQUESTS,
        "error_rate_pct": round(error_rate_pct, 4),
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }


def reset() -> None:
    """Clear in-memory metrics. Intended for isolated tests only."""
    global REQUEST_ATTEMPTS, FAILED_REQUESTS
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    ERRORS.clear()
    FAILED_REQUEST_IDS.clear()
    QUALITY_SCORES.clear()
    REQUEST_ATTEMPTS = 0
    FAILED_REQUESTS = 0
