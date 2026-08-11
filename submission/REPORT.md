# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K3 — E403-C42
- Repository URL: https://github.com/ducTin25/Day13-K3-Observability-E403-C42
- Commit SHA cuối: Chưa chốt; `origin/main` tại thời điểm resolve là `fd5eb32` (đã gồm CP3-C và CP3-D). Cần thay bằng SHA merge cuối cùng trước khi nộp.
- Thành viên và vai trò:
  - Cao Nhật Minh — 2A202601721 — API, middleware và structured logging.
  - Nguyễn Nam Anh — 2A202601703 — Security Engineer, PII scrubbing.
  - Dương Văn Vũ — 2A202601663 — Metrics và dashboard.
  - Trần Anh Thư — 2A202601611 — SLO, alerts và runbook.
  - Nguyễn Đức Tín — 2A202601185 — QA & Chief Investigator.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: `100/100` — 43 records, 22 correlation IDs, không thiếu required field/enrichment và không phát hiện PII leak; xem [`evidence/cp2-validate-logs.txt`](evidence/cp2-validate-logs.txt).
- Tổng số traces: Ít nhất 43 traces trên Langfuse sau CP3; CP2 có 20 traces baseline/practice trong [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md), CP3 có thêm 15 traces official baseline/challenge/recovery trong [`evidence/cp3-e-investigation.md`](evidence/cp3-e-investigation.md), cộng các trace prompt candidate/production.
- Số PII leak còn lại: `0` theo validator và bộ test PII/security.
- Link/đường dẫn dashboard: Contract tại [`../config/dashboard.yaml`](../config/dashboard.yaml); runtime snapshot gồm [baseline HTML](evidence/cp2-dashboard-baseline.html), [incident HTML](evidence/cp2-dashboard-rag-slow.html) và [bảng tổng hợp](evidence/cp2-dashboard-summary.md). Ảnh dashboard runtime vẫn cần bổ sung trước khi nộp.

## 3. Logging và tracing

- Evidence correlation ID: [`evidence/cp2-baseline-logs.jsonl`](evidence/cp2-baseline-logs.jsonl) và [`evidence/cp2-correlation-log.txt`](evidence/cp2-correlation-log.txt) chứng minh `request_received`/`response_sent` có thể nối với trace bằng cùng `correlation_id` và metadata request.
- Evidence PII redaction: Clean log có `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]` và `user_id_hash`; [`evidence/cp2-validate-logs.txt`](evidence/cp2-validate-logs.txt) ghi nhận `Potential PII leaks detected: 0`.
- Evidence trace waterfall: [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md) chứng minh waterfall `agent.run → rag.retrieve` và `agent.run → llm.generate`.
- Giải thích một span đáng chú ý: Với trace practice `140deeeeacae5bbc21e7a21f3b88c876`, `rag.retrieve` mất 2.501 s trên tổng 2.652 s của agent (~94%), trong khi `llm.generate` giữ 0.151 s. Baseline tương ứng có RAG ~0 s và LLM 0.151 s.
- Evidence official challenge: trace `aabc9cc147c22bb125c682479ca03eb2` nối với log bằng `req-9d336808`; RAG mất 2.501 s trên tổng 2.652 s, trong khi recovery trace `8014cca2270ada556ea2b9f9d59c700f` có RAG 0 s và agent 0.151 s.

## 4. Prompt versioning

- Prompt name: `day13-chat` theo prompt contract và cấu hình mặc định của ứng dụng.
- Version/label baseline: Version 1 — labels `baseline`, `production` sau rollback.
- Version/label candidate: Version 2 — labels `candidate`, `latest`.
- Trace ID của mỗi version: baseline v1 `bb19d78c2d1aa24c8731801f6b809615`; candidate v2 `6d4e75fcb32c66ca2d4bf984d1cc9e30`; production v2 `1984d5d04a8c6e13d0bb44ea6bd208e2`; production rollback v1 `28b8becb0b8d543b3fa2663011b90a70`.
- Bằng chứng đổi label hoặc rollback: [`evidence/cp2-prompt-versioning.md`](evidence/cp2-prompt-versioning.md) ghi nhận production được promote sang v2, tạo trace thật, sau đó rollback về v1 và tạo trace xác minh.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract`; xem [`evidence/cp0-dashboard-validator.txt`](evidence/cp0-dashboard-validator.txt).
- Evidence dashboard: [baseline HTML](evidence/cp2-dashboard-baseline.html), [practice incident HTML](evidence/cp2-dashboard-rag-slow.html), [official challenge HTML](evidence/cp3-challenge-dashboard.html), [bảng đối chiếu CP2](evidence/cp2-dashboard-summary.md) và [metric handoff CP3 của C](evidence/cp3-role-c-metrics.md).
- SLO đã chọn và lý do:
  - Latency P95 ≤ 3000 ms, dùng percentile để quan sát tail latency thay vì average.
  - Error rate ≤ 2% để bảo vệ tỷ lệ request thành công.
  - Chi phí ≤ 2.5 USD trong khoảng đánh giá của lab.
  - Quality score trung bình ≥ 0.75; E là owner của quality signal.
  - Production window là 28 ngày; trong lab dùng toàn bộ log của phiên demo/load test làm proxy do traffic giới hạn.
- Alert rules và runbook: Hoàn thành — 4 symptom-based alert (latency P95, error rate, quality, cost) trong [`../config/alert_rules.yaml`](../config/alert_rules.yaml), runbook đầy đủ (SLI/SLO, điều kiện, 3 bước Metrics→Traces→Logs, mitigation/rollback, escalation, điều kiện đóng/verify recovery) trong [`../docs/alerts.md`](../docs/alerts.md). Không hard-code tên incident làm điều kiện alert.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Phạm vi challenge: incident `rag_slow`, affected feature `refund`, latency threshold `2000 ms`.
- Triệu chứng từ metrics: Lượt chạy dashboard/runbook của C/D ghi nhận P95 `6153 ms`, vượt SLO `3000 ms`; lượt trace-controlled của E với cùng 5 official queries/concurrency 5 ghi nhận P95 tăng từ baseline `1414 ms` lên `2652 ms`, vượt threshold challenge `2000 ms`. Cả hai lượt đều có error rate `0.0%` và quality mean `0.86`, nên chỉ tín hiệu latency suy giảm. Xem [`evidence/cp3-challenge-investigation.md`](evidence/cp3-challenge-investigation.md), [`evidence/cp3-role-c-metrics.md`](evidence/cp3-role-c-metrics.md) và [`evidence/cp3-e-investigation.md`](evidence/cp3-e-investigation.md).
- Trace ID liên quan: challenge `aabc9cc147c22bb125c682479ca03eb2`; baseline đối chiếu `b4035f64539e20deb42aef06fd2a60aa`; recovery `8014cca2270ada556ea2b9f9d59c700f`.
- Log line/correlation ID liên quan: trace challenge nối với `req-9d336808`, có feature `refund` và latency `2651 ms`. Lượt C/D còn ghi nhận `req-933d8fb6`, `req-140f2201`, `req-a0aa5316`, `req-8f4be8c3`, `req-13e9d431`; xem [`evidence/cp3-e-correlation-logs.jsonl`](evidence/cp3-e-correlation-logs.jsonl) và [`evidence/cp3-challenge-logs.jsonl`](evidence/cp3-challenge-logs.jsonl).
- Root cause: Runtime trace localize độ trễ vào RAG retrieval: `rag.retrieve` chiếm `2.501/2.652 s` (~94%), trong khi `llm.generate` giữ `0.151 s`, token count bình thường, request không lỗi và quality không giảm. Source được đọc sau bước Metrics → Traces → Logs xác nhận incident chèn delay RAG toàn cục; feature `refund` là phạm vi workload challenge, không phải điều kiện giới hạn incident.
- Fix action: Đã gọi endpoint disable để khôi phục RAG bình thường. Hướng production là retrieval timeout kết hợp cache/fallback an toàn khi dependency vượt latency budget.
- Preventive measure: Alert RAG span P95 theo feature; giữ trace-log correlation; pre-warm/cache prompt để giảm synchronous fetch overhead; dùng windowed metrics để alert tự phản ánh recovery; theo dõi timeout/fallback count; và làm rõ feature scope của incident.
- Recovery verification: Lượt E chạy lại cùng 5 official query/concurrency cho P95 `151 ms`, RAG span `0 s`, agent `0.151 s`; lượt D chạy 10 request sau disable cho P95 `1200 ms`. Cả hai đều dưới SLO `3000 ms` và error rate vẫn `0.0%`.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
| ---------- | --------- | --------- | ----------- |
| A — Cao Nhật Minh | Correlation ID, middleware, metadata context, exception handling và CP2 API verification | [`5bea088`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5bea088), [`5d87342`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5d87342), [PR #3](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/3), [PR #8](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/8) | Nối header/body/log bằng correlation ID, giữ context đúng khi concurrent request và trả lỗi an toàn. |
| B — Nguyễn Nam Anh | PII patterns, recursive scrubbing, `user_id_hash`, trace privacy và security evidence | [`c67b7d8`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/c67b7d8), [`73b7c3f`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73b7c3f), [`3debcf5`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/3debcf5), [PR #6](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/6) | Scrub dữ liệu nhạy cảm trước khi render log/trace, xử lý đệ quy và tránh false positive trên identifier kỹ thuật. |
| C — Dương Văn Vũ | Metrics snapshot/contract, dashboard 6 panel và dashboard evidence baseline/incident/challenge | [`7f8a4b3`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/7f8a4b3), [`96926c5`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/96926c5), [`3d8296e`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/3d8296e), [`a98956a`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/a98956a), [PR #7](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/7), [PR #11](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/11), [PR #13](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/13) | Chuẩn hóa nguồn event/field, dùng percentile cho tail latency và đối chiếu dashboard với dữ liệu JSONL. |
| D — Trần Anh Thư | SLO latency/error/cost/quality, alert rules, runbook và CP3 incident response/recovery | [`73ad7be`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73ad7be), [`c76db70`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/c76db70), [`4ad993a`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/4ad993a), [PR #2](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/2), [PR #10](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/10), [PR #14](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/14) | Chọn SLI theo ảnh hưởng người dùng, định nghĩa sustain window/escalation và xác minh recovery thay vì chỉ tắt cảnh báo. |
| E — Nguyễn Đức Tín | QA baseline/CP1; tracing Agent/RAG/LLM; prompt v1/v2; official challenge investigation; trace-log correlation và recovery verification | [`55e43e7`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/55e43e7), [`a6ab966`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/a6ab966), [`e86b968`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/e86b968), [PR #1](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/1), [PR #9](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/9), [PR #12](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/12) | Điều tra Metrics → Traces → Logs bằng evidence thật, khoanh vùng RAG và chỉ đóng incident sau khi cùng workload chứng minh recovery. |
