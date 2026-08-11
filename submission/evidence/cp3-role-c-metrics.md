# CP3 — Role C metric handoff

## Official challenge execution

- Challenge ID: `day13-k3-observability-v1`
- Incident: `rag_slow`
- Affected feature: `refund`
- Command: `python scripts/load_test.py --challenge --concurrency 5`
- Metric time window: `2026-08-11T05:05 UTC`
- The incident was disabled after evidence collection.

## Symptom from metrics

| Signal | Baseline CP2 | Official challenge | Interpretation |
|---|---:|---:|---|
| Latency P95 | 151 ms | 2653 ms | Increase of 2502 ms; exceeds challenge threshold 2000 ms |
| Latency P99 | 151 ms | 2653 ms | Tail latency is elevated |
| Traffic | 10 requests baseline | 5 official requests; peak 5 req/min | Traffic remains present |
| Error rate | 0.0% | 0.0% | No request-failure symptom |
| Quality mean | 0.88 | 0.86 | Not the primary observed symptom |

The P95 challenge value is below the dashboard SLO line of 3000 ms, but above the released challenge threshold of 2000 ms. Metrics therefore identify a latency degradation, not a root cause.

## Correlation IDs for E's trace/log investigation

| Correlation ID | Response log line | `response_sent.latency_ms` |
|---|---:|---:|
| `req-5f57363a` | 4 | 2651 |
| `req-33c9924b` | 6 | 2651 |
| `req-7644f60a` | 8 | 2652 |
| `req-33bedc14` | 10 | 2652 |
| `req-84c54330` | 12 | 2653 |

Use the selected correlation ID in trace metadata and the linked JSONL record to determine the abnormal span. Do not claim a root cause from this metric evidence alone.

## Artifacts

- [Challenge dashboard HTML](cp3-challenge-dashboard.html)
- [Challenge JSONL log](cp3-challenge-logs.jsonl)
