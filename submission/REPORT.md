# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: K3 — E403-C42
- Repository URL: https://github.com/ducTin25/Day13-K3-Observability-E403-C42
- Commit SHA cuối: Chưa chốt; HEAD tại thời điểm cập nhật báo cáo là `ec66dd9`.
- Thành viên và vai trò:
  - Cao Nhật Minh — 2A202601721 — API, middleware và structured logging.
  - Nguyễn Nam Anh — 2A202601703 — Security Engineer, PII scrubbing.
  - Dương Văn Vũ — 2A202601663 — Metrics và dashboard.
  - Trần Anh Thư — 2A202601611 — SLO, alerts và runbook.
  - Nguyễn Đức Tín — 2A202601185 — QA & Chief Investigator.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: `100/100` trên `data/logs_cp1_clean.jsonl` — 21 records hợp lệ, 10 correlation IDs, không thiếu enrichment.
- Tổng số traces: Ít nhất 24 traces CP2 trên Langfuse; 20 traces baseline/practice được liệt kê trong [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md), cộng các trace prompt candidate/production.
- Số PII leak còn lại: `0` theo `validate_logs.py` trên clean log.
- Link/đường dẫn dashboard: Contract tại [`../config/dashboard.yaml`](../config/dashboard.yaml); chưa có ảnh dashboard runtime trong `submission/evidence/`.

## 3. Logging và tracing

- Evidence correlation ID: [`../data/logs_cp1_clean.jsonl`](../data/logs_cp1_clean.jsonl) chứa 10 correlation IDs duy nhất; mỗi cặp `request_received`/`response_sent` giữ cùng metadata của request.
- Evidence PII redaction: Clean log có `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]` và `user_id_hash`; validator báo `Potential PII leaks detected: 0`.
- Evidence trace waterfall: [`evidence/cp2-tracing-evidence.md`](evidence/cp2-tracing-evidence.md) chứng minh waterfall `agent.run → rag.retrieve` và `agent.run → llm.generate`.
- Giải thích một span đáng chú ý: Với trace practice `140deeeeacae5bbc21e7a21f3b88c876`, `rag.retrieve` mất 2.501 s trên tổng 2.652 s của agent (~94%), trong khi `llm.generate` giữ 0.151 s. Baseline tương ứng có RAG ~0 s và LLM 0.151 s.

## 4. Prompt versioning

- Prompt name: `day13-chat` theo prompt contract và cấu hình mặc định của ứng dụng.
- Version/label baseline: Version 1 — labels `baseline`, `production` sau rollback.
- Version/label candidate: Version 2 — labels `candidate`, `latest`.
- Trace ID của mỗi version: baseline v1 `bb19d78c2d1aa24c8731801f6b809615`; candidate v2 `6d4e75fcb32c66ca2d4bf984d1cc9e30`; production v2 `1984d5d04a8c6e13d0bb44ea6bd208e2`; production rollback v1 `28b8becb0b8d543b3fa2663011b90a70`.
- Bằng chứng đổi label hoặc rollback: [`evidence/cp2-prompt-versioning.md`](evidence/cp2-prompt-versioning.md) ghi nhận production được promote sang v2, tạo trace thật, sau đó rollback về v1 và tạo trace xác minh.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract`.
- Evidence dashboard: [baseline HTML](evidence/cp2-dashboard-baseline.html), [incident HTML](evidence/cp2-dashboard-rag-slow.html) và [bảng đối chiếu JSONL](evidence/cp2-dashboard-summary.md).
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
- Triệu chứng từ metrics: `GET /metrics` sau khi chạy `inject_incident.py` + `load_test.py --challenge --concurrency 5` báo `latency_p50=4194ms, latency_p95=6153ms` (ngưỡng SLO P95 3000ms), `error_rate_pct=0%`, `quality_avg=0.86`, `total_cost_usd=0.0088` — chỉ Alert 1 (Latency P95 Breach, critical) trigger, xem [`evidence/cp3-challenge-investigation.md`](evidence/cp3-challenge-investigation.md).
- Trace ID liên quan: chưa lấy được qua Langfuse Read API (401 khi gọi `trace.list` dù ingestion vẫn hoạt động) — cần E/A mở Langfuse UI lọc tag `refund`/khung giờ `05:14:30–05:14:53Z (2026-08-11)` để bổ sung trace ID trực quan.
- Log line/correlation ID liên quan: 5 correlation ID `req-933d8fb6, req-140f2201, req-a0aa5316, req-8f4be8c3, req-13e9d431` (feature `refund`, latency 3800–6153ms), chi tiết trong evidence file trên.
- Root cause: `app/mock_rag.py` chèn `time.sleep(2.5)` trong `retrieve()` khi `STATE["rag_slow"]` bật — áp dụng cho toàn bộ RAG, không riêng feature `refund` (feature này chỉ trùng vì toàn bộ query challenge đều gắn `feature=refund`). Xác nhận bằng token count bình thường (loại trừ nguyên nhân LLM sinh output dài) và đối chiếu source code sau khi đã có giả thuyết từ metrics/log.
- Fix action: `POST /incidents/rag_slow/disable`; xác minh recovery bằng 10 request tiếp theo có P95 = 1200ms (< 3000ms ngưỡng SLO), error_rate vẫn 0%.
- Preventive measure (bàn giao E đưa vào phần tổng hợp): (1) `resolve_prompt()` gọi Langfuse `get_prompt` đồng bộ mỗi request, làm baseline latency tăng từ ~150ms lên ~1.1s sau khi bật tracing thật — nên fetch bất đồng bộ hoặc pre-warm cache khi startup; (2) `/metrics` cộng dồn latency từ lúc start process, không có time window, nên sau khi fix P95 hiển thị vẫn giữ giá trị cũ — cần windowed metrics; (3) `rag_slow` hiện là incident toàn cục (không lọc theo feature) — nếu muốn scope theo feature cần sửa `mock_rag.py`.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc                                                           | Commit/PR                                                                                                                                                            | Điều đã học                                                                       |
| ---------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| A          | Correlation ID, middleware, exception handling và clean CP1 log     | [`5bea088`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5bea088)                                                                              | Nối header/body/log và giữ response lỗi an toàn.                                  |
| B          | PII scrubbing và security evidence                                  | Chưa có commit riêng sau phân công trong lịch sử hiện tại                                                                                                            | Cần scrub dữ liệu trước khi JSON được render và ghi file.                         |
| C          | Metrics contract và CP0 dashboard evidence                          | [`7f8a4b3`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/7f8a4b3)                                                                              | Chuẩn hóa nguồn event/field trước khi dựng dashboard.                             |
| D          | SLO latency, error, cost và quality                                 | [`73ad7be`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73ad7be)                                                                              | Chọn SLI theo trải nghiệm người dùng và ghi rõ giả định window.                   |
| E          | QA baseline; tracing Agent/RAG/LLM; prompt v1/v2, promote/rollback; trace-log correlation | [`55e43e7`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/55e43e7), [PR #1](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/1); CP2 commit đang chờ tạo | Điều tra từ phạm vi rộng đến hẹp, liên kết trace với log và quản lý prompt bằng version/label thay vì giả metadata. |
