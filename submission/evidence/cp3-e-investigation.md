# CP3 Evidence — Official Challenge Investigation (Member E)

## Scope and integrity

- Owner: Nguyễn Đức Tín — Member E, QA & Chief Investigator.
- Challenge ID: `day13-k3-observability-v1`.
- Cohort: `K3`.
- Incident: `rag_slow`.
- Affected feature: `refund`.
- Released symptom threshold: latency P95 `2000 ms`.
- `config/challenge.json` matched `upstream/main` before execution and was not edited.
- Run time: `2026-08-11T05:18:42Z` to `2026-08-11T05:19:00Z`.
- All three windows used the same five official queries with concurrency 5.

The standard run on port 8000 used `python scripts/inject_incident.py` and
`python scripts/load_test.py --challenge --concurrency 5`. A second isolated
run on port 8012 used the same official workload and the equivalent incident
control endpoints so the Langfuse batch could be flushed without stopping the
existing port-8000 process.

## Metrics — detect the symptom

Metrics below were independently calculated from the five `response_sent`
records in each isolated log window, not from the cumulative in-memory P95.

| Window | Incident | Traffic | Error rate | P50 | P95 | Quality mean |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | off | 5 | 0.0% | 151 ms | 1414 ms | 0.86 |
| Official challenge | on | 5 | 0.0% | 2651 ms | 2652 ms | 0.86 |
| Recovery | off | 5 | 0.0% | 151 ms | 151 ms | 0.86 |

The challenge P95 exceeded the released threshold by `652 ms` and increased
`1238 ms` relative to the baseline window. Error rate and quality did not
degrade, so the observed symptom was latency rather than failure or output
quality. The single 1414 ms baseline outlier was prompt-fetch/cold-start
overhead; four of five baseline agent traces were approximately 151 ms.

Raw load output is in [`cp3-e-load-output.txt`](cp3-e-load-output.txt).

## Traces — localize the latency

### Trace inventory

| Window | Trace ID | Correlation ID | Agent duration |
|---|---|---|---:|
| Baseline | `5d836dd9108c8b9709405b51afd17701` | `req-f5c7ae45` | 1.415 s |
| Baseline | `b4035f64539e20deb42aef06fd2a60aa` | `req-e0e1d3b4` | 0.151 s |
| Baseline | `ea4c5641ffee683212bcba9cd06bc54b` | `req-2ebfe97c` | 0.152 s |
| Baseline | `149df9104a96254c3f7bcbf1e2f866e0` | `req-47575f23` | 0.151 s |
| Baseline | `8f4ca5eb4cd8081814b726eee407ab0e` | `req-3262b4e1` | 0.151 s |
| Challenge | `aabc9cc147c22bb125c682479ca03eb2` | `req-9d336808` | 2.652 s |
| Challenge | `eab6af35efe43d0d0d6e300d592fa90d` | `req-f8faa066` | 2.652 s |
| Challenge | `aa5ea8990f86edc393733a9a9ada0420` | `req-1b88ea82` | 2.652 s |
| Challenge | `c496c662b8e39036916c108a1e457098` | `req-047b313e` | 2.652 s |
| Challenge | `f751fb8a67e6e15980e5fc1783c15eb8` | `req-61bbe6d4` | 2.651 s |
| Recovery | `8014cca2270ada556ea2b9f9d59c700f` | `req-3ac12bb5` | 0.151 s |
| Recovery | `437e838f0decbdf22e50be434bd227ff` | `req-dd6cf23f` | 0.151 s |
| Recovery | `968dc734041799e15b73e26fdb189a56` | `req-bafa34e5` | 0.151 s |
| Recovery | `a62f8feb6065a01770137be1726add24` | `req-5d6ee495` | 0.151 s |
| Recovery | `65b81da7dab6923cfedcbce9a4a019bd` | `req-55a2c6e4` | 0.151 s |

### Representative waterfall

Official challenge trace `aabc9cc147c22bb125c682479ca03eb2`:

| Observation | Parent | Duration | Notes |
|---|---|---:|---|
| `agent.run` | root | 2.652 s | production prompt v1 |
| `rag.retrieve` | `agent.run` | 2.501 s | about 94% of agent latency |
| `llm.generate` | `agent.run` | 0.151 s | model `claude-sonnet-4-5` |

The LLM generation used 34 prompt tokens and 120 completion tokens, with total
cost USD 0.001902. Observation input/output fields were `null`, so no raw
request or answer was captured.

For comparison:

- Baseline trace `b4035f64539e20deb42aef06fd2a60aa`: RAG 0 s, LLM 0.151 s, agent 0.151 s.
- Recovery trace `8014cca2270ada556ea2b9f9d59c700f`: RAG 0 s, LLM 0.151 s, agent 0.151 s.

## Logs — confirm the affected request

The challenge trace carries correlation ID `req-9d336808`. The exact
`request_received` and `response_sent` records in
[`cp3-e-correlation-logs.jsonl`](cp3-e-correlation-logs.jsonl) show:

- feature `refund`;
- API latency `2651 ms`;
- HTTP workload succeeded and no `request_failed` event occurred;
- metadata remained enriched and PII-safe.

The same file includes baseline `req-e0e1d3b4`, recovery `req-3ac12bb5`, and
the `incident_enabled`/`incident_disabled` control events.

## Root cause and response

### Root cause

The three evidence layers agree:

1. Metrics show a latency-only degradation above the challenge threshold.
2. Every challenge trace localizes approximately 2.5 seconds to
   `rag.retrieve`, while `llm.generate` remains approximately 0.151 seconds.
3. The correlated log confirms the affected request belongs to feature
   `refund` and completed without an application error.

Therefore the incident root cause is degraded RAG retrieval latency on the
official refund workload, not the LLM, error handling, cost, or quality path.

### Mitigation and fix action

- Immediate mitigation performed: disable `rag_slow` after evidence capture.
- Fix action for the lab: restore the normal RAG path and keep the incident
  flag disabled.
- Production-oriented fix: enforce a retrieval timeout and return a safe
  cached/fallback document set when the retrieval dependency exceeds its
  latency budget.

### Preventive measures

- Alert on RAG span P95 by feature before end-to-end latency breaches the user
  SLO.
- Keep `correlation_id` on traces and structured logs for deterministic
  Metrics → Traces → Logs investigation.
- Add a regression workload that compares baseline and recovery with identical
  official queries and concurrency.
- Track retrieval timeout/fallback count and include it in the runbook.

## Recovery verification

After `incident_disabled` at `2026-08-11T05:18:59.601Z`, the same five queries
were rerun at concurrency 5:

- P95 returned from 2652 ms to 151 ms, below both the 2000 ms challenge
  threshold and the 3000 ms dashboard SLO.
- Representative RAG span returned from 2.501 s to 0 s.
- Representative agent duration returned from 2.652 s to 0.151 s.
- Error rate remained 0.0% and quality mean remained 0.86.
- Final health state had all incident flags disabled.

This is recovery evidence under the same workload, not merely confirmation that
the incident flag changed state.

Final tests, log validation, dashboard validation, health state, and security
scan are recorded in [`cp3-e-validation.txt`](cp3-e-validation.txt).

## UI evidence note

Langfuse API returned all trace and observation data above. The automated
browser runtime had no available browser, so UI screenshots were not fabricated;
a manual Langfuse waterfall screenshot should still be added before final
submission if the grader requires image evidence.
