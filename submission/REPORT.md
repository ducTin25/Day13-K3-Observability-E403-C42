# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K3 — E403-C42
- Repository URL: https://github.com/ducTin25/Day13-K3-Observability-E403-C42
- Commit SHA cuối: Chưa chốt; `origin/main` tại thời điểm cập nhật báo cáo là `8e5a066` (merge PR #12 của E). Cần thay bằng SHA cuối cùng sau khi hoàn tất CP3.
- Thành viên và vai trò:
  - Cao Nhật Minh — 2A202601721 — API, middleware và structured logging.
  - Nguyễn Nam Anh — 2A202601703 — Security Engineer, PII scrubbing.
  - Dương Văn Vũ — 2A202601663 — Metrics và dashboard.
  - Trần Anh Thư — 2A202601611 — SLO, alerts và runbook.
  - Nguyễn Đức Tín — 2A202601185 — QA & Chief Investigator.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: `100/100` — 43 records, 22 correlation IDs, không thiếu required field/enrichment và không phát hiện PII leak; xem [`evidence/cp2-validate-logs.txt`](evidence/cp2-validate-logs.txt).
- Tổng số traces: Ít nhất 24 traces CP2 trên Langfuse; 20 traces baseline/practice được liệt kê trong [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md), cộng các trace prompt candidate/production.
- Số PII leak còn lại: `0` theo validator và bộ test PII/security.
- Link/đường dẫn dashboard: Contract tại [`../config/dashboard.yaml`](../config/dashboard.yaml); runtime snapshot gồm [baseline HTML](evidence/cp2-dashboard-baseline.html), [incident HTML](evidence/cp2-dashboard-rag-slow.html) và [bảng tổng hợp](evidence/cp2-dashboard-summary.md). Ảnh dashboard runtime vẫn cần bổ sung trước khi nộp.

## 3. Logging và tracing

- Evidence correlation ID: [`evidence/cp2-baseline-logs.jsonl`](evidence/cp2-baseline-logs.jsonl) và [`evidence/cp2-correlation-log.txt`](evidence/cp2-correlation-log.txt) chứng minh `request_received`/`response_sent` có thể nối với trace bằng cùng `correlation_id` và metadata request.
- Evidence PII redaction: Clean log có `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]` và `user_id_hash`; [`evidence/cp2-validate-logs.txt`](evidence/cp2-validate-logs.txt) ghi nhận `Potential PII leaks detected: 0`.
- Evidence trace waterfall: [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md) chứng minh waterfall `agent.run → rag.retrieve` và `agent.run → llm.generate`.
- Giải thích một span đáng chú ý: Với trace practice `140deeeeacae5bbc21e7a21f3b88c876`, `rag.retrieve` mất 2.501 s trên tổng 2.652 s của agent (~94%), trong khi `llm.generate` giữ 0.151 s. Baseline tương ứng có RAG ~0 s và LLM 0.151 s.

## 4. Prompt versioning

- Prompt name: `day13-chat` theo prompt contract và cấu hình mặc định của ứng dụng.
- Version/label baseline: Version 1 — labels `baseline`, `production` sau rollback.
- Version/label candidate: Version 2 — labels `candidate`, `latest`.
- Trace ID của mỗi version: baseline v1 `bb19d78c2d1aa24c8731801f6b809615`; candidate v2 `6d4e75fcb32c66ca2d4bf984d1cc9e30`; production v2 `1984d5d04a8c6e13d0bb44ea6bd208e2`; production rollback v1 `28b8becb0b8d543b3fa2663011b90a70`.
- Bằng chứng đổi label hoặc rollback: [`evidence/cp2-prompt-versioning.md`](evidence/cp2-prompt-versioning.md) ghi nhận production được promote sang v2, tạo trace thật, sau đó rollback về v1 và tạo trace xác minh.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract`; xem [`evidence/cp0-dashboard-validator.txt`](evidence/cp0-dashboard-validator.txt).
- Evidence dashboard: [baseline HTML](evidence/cp2-dashboard-baseline.html), [incident HTML](evidence/cp2-dashboard-rag-slow.html) và [bảng đối chiếu JSONL](evidence/cp2-dashboard-summary.md).
- SLO đã chọn và lý do:
  - Latency P95 ≤ 3000 ms, dùng percentile để quan sát tail latency thay vì average.
  - Error rate ≤ 2% để bảo vệ tỷ lệ request thành công.
  - Chi phí ≤ 2.5 USD trong khoảng đánh giá của lab.
  - Quality score trung bình ≥ 0.75; E là owner của quality signal.
  - Production window là 28 ngày; trong lab dùng toàn bộ log của phiên demo/load test làm proxy do traffic giới hạn.
- Alert rules và runbook: Đã hoàn thành tại [`../config/alert_rules.yaml`](../config/alert_rules.yaml) và [`../docs/alerts.md`](../docs/alerts.md), gồm latency, error rate, quality và cost; mỗi alert có threshold/window, owner, escalation, mitigation và điều kiện recovery.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Phạm vi challenge: incident `rag_slow`, affected feature `refund`, latency threshold `2000 ms`.
- Triệu chứng từ metrics: Chưa chạy và lưu evidence official challenge. Practice `rag_slow` cho thấy RAG tăng từ xấp xỉ 0 s lên 2.501 s, nhưng không được dùng thay cho official challenge.
- Trace ID liên quan: Chưa thu thập.
- Log line/correlation ID liên quan: Chưa thu thập cho official challenge.
- Root cause: Chưa kết luận; giả thuyết RAG chậm phải được kiểm chứng bằng Metrics → Traces → Logs runtime.
- Fix action: Chưa đề xuất trước khi có đủ evidence runtime.
- Preventive measure: Chưa đề xuất trước khi có đủ evidence runtime.
- Recovery verification: Chưa có lượt chạy lại official workload sau khi disable incident.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
| ---------- | --------- | --------- | ----------- |
| A — Cao Nhật Minh | Correlation ID, middleware, metadata context, exception handling và CP2 API verification | [`5bea088`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5bea088), [`5d87342`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5d87342), [PR #3](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/3), [PR #8](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/8) | Nối header/body/log bằng correlation ID, giữ context đúng khi concurrent request và trả lỗi an toàn. |
| B — Nguyễn Nam Anh | PII patterns, recursive scrubbing, `user_id_hash`, trace privacy và security evidence | [`c67b7d8`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/c67b7d8), [`73b7c3f`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73b7c3f), [`3debcf5`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/3debcf5), [PR #6](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/6) | Scrub dữ liệu nhạy cảm trước khi render log/trace, xử lý đệ quy và tránh false positive trên identifier kỹ thuật. |
| C — Dương Văn Vũ | Metrics snapshot/contract, dashboard 6 panel và dashboard evidence baseline/incident | [`7f8a4b3`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/7f8a4b3), [`96926c5`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/96926c5), [`3d8296e`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/3d8296e), [PR #7](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/7), [PR #11](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/11) | Chuẩn hóa nguồn event/field, dùng percentile cho tail latency và đối chiếu dashboard với dữ liệu JSONL. |
| D — Trần Anh Thư | SLO latency/error/cost/quality, alert rules và runbook điều tra/recovery | [`73ad7be`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73ad7be), [`c76db70`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/c76db70), [PR #2](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/2), [PR #10](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/10) | Chọn SLI theo ảnh hưởng người dùng, định nghĩa sustain window/escalation và xác minh recovery thay vì chỉ tắt cảnh báo. |
| E — Nguyễn Đức Tín | QA baseline/CP1; tracing Agent/RAG/LLM; prompt v1/v2, promote/rollback; load test và trace-log correlation | [`55e43e7`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/55e43e7), [`a6ab966`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/a6ab966), [`e86b968`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/e86b968), [PR #1](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/1), [PR #9](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/9), [PR #12](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/12) | Điều tra từ phạm vi rộng đến hẹp, liên kết trace với log và quản lý prompt bằng version/label thật thay vì giả metadata. |
