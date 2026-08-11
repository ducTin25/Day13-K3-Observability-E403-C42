# Thành viên C — Metrics & Dashboard

## Phạm vi phụ trách

Thành viên C chịu trách nhiệm định nghĩa và đo `error_rate_pct`, kiểm tra metrics CP1/CP2, dựng dashboard runtime đủ 6 nhóm chỉ số và cung cấp dashboard evidence.

## Trạng thái repo hiện tại

- `app/metrics.py` có traffic, latency, token, cost, quality và error breakdown.
- Snapshot chưa trả trực tiếp `error_rate_pct`.
- `record_request()` chỉ tăng traffic cho request thành công; `record_error()` tách riêng, nên mẫu số error rate cần được định nghĩa rõ.
- `config/dashboard.yaml` đã có contract hợp lệ cho 6 panel.
- Validator config đang pass nhưng repo chưa có bằng chứng dashboard runtime.
- Nguồn chuẩn bắt buộc là `data/logs.jsonl`, không phải Langfuse metrics.

## Checkpoint 0 — Baseline metrics

### Task

- Chạy validator dashboard để xác nhận contract 6/6.
- Đọc baseline log và ghi nhận những field còn thiếu.
- Thống nhất với A định nghĩa một request attempt, success và failure.
- Ghi baseline latency, traffic, error, token, cost và quality nếu dữ liệu đủ.

### Acceptance criteria

- Có bảng mapping event/field cho 6 panel.
- Có định nghĩa error rate bằng lời và công thức.
- Không dùng dữ liệu giả chỉ để vượt validator.

### Blocker/dependency

- Baseline log hiện thiếu correlation ID và enrichment; A phải sửa trước khi dùng làm evidence cuối.
- Validator pass chỉ chứng minh YAML đúng, không chứng minh dashboard runtime đúng.

## Checkpoint 1 — Định nghĩa và đo `error_rate_pct`

### Task C1 — Chốt metric contract

Định nghĩa đề xuất:

```text
error_rate_pct = failed_requests / total_request_attempts * 100
```

- Chốt request nào thuộc mẫu số: chỉ `/chat` hay toàn API.
- Chốt 4xx validation có tính là failure hay không.
- Chốt error count theo request, không theo số log line.
- Bảo đảm một request lỗi chỉ được đếm một lần.
- Quy định hành vi khi mẫu số bằng 0: trả `0.0`, không chia cho 0.

### Task C2 — Hoàn thiện metrics API

- Bổ sung dữ liệu cần thiết để `/metrics` trả `error_rate_pct`.
- Giữ `error_breakdown` theo `error_type`.
- Kiểm tra traffic counter có phản ánh đúng tổng request attempt theo contract.
- Thêm test: 0 request, toàn success, có failure, nhiều error type và duplicate protection ở lớp tích hợp.

### Acceptance criteria

- `/metrics` trả error rate dạng phần trăm nhất quán với log.
- Error rate từ in-memory metrics và từ JSONL cho cùng workload phải khớp.
- Không có trường hợp error rate vượt 100% do sai mẫu số hoặc double count.

### Blocker/dependency

- Phụ thuộc A phát event lifecycle nhất quán và gọi `record_error()` đúng một lần.
- Cần quyết định chung về validation error trước khi code để tránh sửa lại dashboard/query.

## Checkpoint 2 — Dashboard 6 nhóm chỉ số

### Task C1 — Dựng dashboard runtime

Dùng `data/logs.jsonl` và dựng đúng 6 panel:

1. Latency P50/P95/P99 từ `response_sent.latency_ms`.
2. Traffic count/request per minute từ `request_received`.
3. Error rate và breakdown từ `request_received`, `request_failed`, `error_type`.
4. Cost theo phút và tổng từ `response_sent.cost_usd`.
5. Tổng input/output token từ `tokens_in`, `tokens_out`.
6. Mean quality proxy từ `quality_score`.

### Task C2 — Presentation contract

- Time range mặc định 60 phút.
- Refresh 30 giây nếu công cụ hỗ trợ.
- Hiển thị đúng đơn vị.
- Hiển thị threshold/SLO line theo `config/dashboard.yaml`.
- Giữ lớp chính ở 6 panel, không thêm biểu đồ gây nhiễu.

### Task C3 — Verify runtime

- Chạy `python scripts/validate_dashboard.py` và lưu output `6/6 panel`.
- Chụp dashboard baseline.
- Bật practice `rag_slow`, chạy cùng workload/concurrency và xác nhận P95 tăng.
- Kiểm tra tổng token/cost/traffic/error bằng tính tay hoặc script độc lập trên JSONL.
- Chụp screenshot thấy rõ panel title, time range, unit và threshold.

### Acceptance criteria

- Validator báo hợp lệ 6/6.
- Dashboard runtime lấy dữ liệu thật từ JSONL.
- Sáu phép tổng hợp khớp dữ liệu nguồn.
- Evidence thể hiện được thay đổi baseline → incident.

### Blocker/dependency

- Phụ thuộc A tạo log lifecycle chính xác và B bảo đảm log không có PII.
- SLO line và alert thresholds cần thống nhất với D.
- Cần chọn công cụ dashboard runtime; YAML không tự tạo dashboard.

## Checkpoint 3 — Challenge

### Task

- Chạy/refresh dashboard trên cửa sổ challenge.
- Chỉ ra metric triệu chứng đầu tiên và time range cụ thể.
- Với challenge `rag_slow`, kiểm tra P95 so với ngưỡng 2000 ms trong file challenge và SLO 3000 ms của dashboard.
- Bàn giao timestamp/time window và request/correlation ID bất thường cho E.
- Không kết luận root cause chỉ từ metrics.

### Blocker/dependency

- Challenge đã release.
- Root cause phụ thuộc E mở trace và A cung cấp correlation ID/log.

## Hoàn tất và bàn giao

- Commit/PR cho metrics, tests và dashboard artifact nếu có source.
- Công thức và quyết định mẫu số của `error_rate_pct`.
- Output validator 6/6.
- Screenshot dashboard baseline và challenge.
- Bảng đối chiếu số liệu dashboard với JSONL.
- Ghi phần đóng góp cá nhân và commit SHA vào `submission/REPORT.md`.

## Thứ tự thực hiện đề xuất

1. Chốt metric contract với A/D.
2. Hoàn thiện `error_rate_pct` và tests.
3. Nhận log sạch từ A/B.
4. Dựng và verify 6 panel.
5. Đồng bộ threshold với D.
6. Cung cấp metric evidence cho E.
