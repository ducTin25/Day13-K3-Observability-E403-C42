# CP0 baseline metrics

## Workload

- Date: 2026-08-11
- Command: `python scripts/load_test.py --concurrency 5`
- Source of dashboard calculations: `data/logs.jsonl`
- In-memory API metric source: `GET /metrics`
- Result: 10 successful `/chat` request attempts; no failed requests.

## Baseline from `GET /metrics`

| Metric | Value |
|---|---:|
| Traffic / total request attempts | 10 |
| Failed requests | 0 |
| Error rate | 0.0% |
| Latency P50 | 150 ms |
| Latency P95 | 150 ms |
| Latency P99 | 150 ms |
| Total cost | USD 0.0197 |
| Input tokens | 330 |
| Output tokens | 1248 |
| Quality average | 0.88 |

## Dashboard event/field mapping

| Panel | Event | Fields | Aggregation |
|---|---|---|---|
| Latency | `response_sent` | `latency_ms` | P50, P95, P99 |
| Traffic | `request_received` | `event` | count, requests/minute |
| Errors | `request_received`, `request_failed` | `error_type` | `failed / attempts * 100`, count by error type |
| Cost | `response_sent` | `cost_usd` | sum per minute, total |
| Tokens | `response_sent` | `tokens_in`, `tokens_out` | sum by field |
| Quality | `response_sent` | `quality_score` | mean |

## Error rate contract

`error_rate_pct = failed_requests / total_request_attempts * 100`.

An attempt is one `/chat` request that reaches the route handler. A failed request is counted at most once by correlation ID. When there are no attempts, the result is `0.0`.

## Log readiness gaps found in this baseline

`python scripts/validate_logs.py` analyzed 22 records and reported 20 API records with missing required context, zero unique correlation IDs, and 20 records missing enrichment. The current response IDs are `MISSING`.

This baseline is valid for CP0 metric discovery, but it is **not final dashboard evidence**. A must add correlation ID and request enrichment; B must re-validate PII safety before CP2 dashboard evidence is captured.
