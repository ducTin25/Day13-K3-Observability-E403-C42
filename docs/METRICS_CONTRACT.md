# Metrics contract

## Error rate

`error_rate_pct = failed_requests / total_request_attempts * 100`.

- Scope: requests to `/chat` that reach the route handler.
- An attempt is counted once, immediately before `request_received` is logged.
- A failed request is counted once by its correlation ID, even if more than one error path tries to record it.
- Pydantic validation errors (422) occur before the route handler and are not included in this CP1 metric. If the team later decides to include them, A must emit both lifecycle events and call the same attempt/failure metrics functions.
- With no attempts, `error_rate_pct` is `0.0`.

`traffic` in `/metrics` is the same value as `total_request_attempts`. The JSONL dashboard uses `request_received` as its denominator and `request_failed` as its numerator, so it follows this same contract.
