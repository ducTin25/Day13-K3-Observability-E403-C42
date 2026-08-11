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
- Tổng số traces: Chưa thu thập evidence Langfuse; chưa thể xác nhận yêu cầu tối thiểu 10 traces.
- Số PII leak còn lại: `0` theo `validate_logs.py` trên clean log.
- Link/đường dẫn dashboard: Contract tại [`../config/dashboard.yaml`](../config/dashboard.yaml); chưa có ảnh dashboard runtime trong `submission/evidence/`.

## 3. Logging và tracing

- Evidence correlation ID: [`../data/logs_cp1_clean.jsonl`](../data/logs_cp1_clean.jsonl) chứa 10 correlation IDs duy nhất; mỗi cặp `request_received`/`response_sent` giữ cùng metadata của request.
- Evidence PII redaction: Clean log có `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]` và `user_id_hash`; validator báo `Potential PII leaks detected: 0`.
- Evidence trace waterfall: Chưa thu thập; cần trace thể hiện `agent → RAG → LLM`.
- Giải thích một span đáng chú ý: Chưa có sub-component trace runtime để kết luận.

## 4. Prompt versioning

- Prompt name: `day13-chat` theo prompt contract và cấu hình mặc định của ứng dụng.
- Version/label baseline: Chưa có evidence Langfuse.
- Version/label candidate: Chưa có evidence Langfuse.
- Trace ID của mỗi version: Chưa thu thập.
- Bằng chứng đổi label hoặc rollback: Chưa thu thập.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract`.
- Evidence dashboard: [baseline HTML](evidence/cp2-dashboard-baseline.html), [incident HTML](evidence/cp2-dashboard-rag-slow.html) và [bảng đối chiếu JSONL](evidence/cp2-dashboard-summary.md).
- SLO đã chọn và lý do:
  - Latency P95 ≤ 3000 ms, dùng percentile để quan sát tail latency thay vì average.
  - Error rate ≤ 2% để bảo vệ tỷ lệ request thành công.
  - Chi phí ≤ 2.5 USD trong khoảng đánh giá của lab.
  - Quality score trung bình ≥ 0.75; E là owner của quality signal.
  - Production window là 28 ngày; trong lab dùng toàn bộ log của phiên demo/load test làm proxy do traffic giới hạn.
- Alert rules và runbook: Chưa hoàn thành; [`../config/alert_rules.yaml`](../config/alert_rules.yaml) và [`../docs/alerts.md`](../docs/alerts.md) vẫn còn placeholder/TODO.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Phạm vi challenge: incident `rag_slow`, affected feature `refund`, latency threshold `2000 ms`.
- Triệu chứng từ metrics: Chưa chạy và lưu evidence official challenge.
- Trace ID liên quan: Chưa thu thập.
- Log line/correlation ID liên quan: Chưa thu thập cho official challenge.
- Root cause: Chưa kết luận; giả thuyết RAG chậm phải được kiểm chứng bằng Metrics → Traces → Logs runtime.
- Fix action: Chưa đề xuất trước khi có đủ evidence runtime.
- Preventive measure: Chưa đề xuất trước khi có đủ evidence runtime.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc                                                           | Commit/PR                                                                                                                                                            | Điều đã học                                                                       |
| ---------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| A          | Correlation ID, middleware, exception handling và clean CP1 log     | [`5bea088`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/5bea088)                                                                              | Nối header/body/log và giữ response lỗi an toàn.                                  |
| B          | PII scrubbing và security evidence                                  | Chưa có commit riêng sau phân công trong lịch sử hiện tại                                                                                                            | Cần scrub dữ liệu trước khi JSON được render và ghi file.                         |
| C          | Metrics contract và CP0 dashboard evidence                          | [`7f8a4b3`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/7f8a4b3)                                                                              | Chuẩn hóa nguồn event/field trước khi dựng dashboard.                             |
| D          | SLO latency, error, cost và quality                                 | [`73ad7be`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/73ad7be)                                                                              | Chọn SLI theo trải nghiệm người dùng và ghi rõ giả định window.                   |
| E          | QA test plan, baseline CP0 và phân tách practice/official challenge | [`55e43e7`](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/commit/55e43e7), [PR #1](https://github.com/ducTin25/Day13-K3-Observability-E403-C42/pull/1) | Điều tra từ phạm vi rộng đến hẹp và luôn gắn kết luận với evidence tái chạy được. |
