# CP0 Baseline — QA & Chief Investigator

## Thông tin lần chạy

- Ngày chạy: 2026-08-11
- Môi trường: local, `http://127.0.0.1:8000`
- Nguồn workload: `data/sample_queries.jsonl` (practice)
- Official challenge: không chạy trong baseline này
- Incident flags khi health check: `rag_slow=false`, `tool_fail=false`, `cost_spike=false`

## Kết quả

### Health check

```json
{"ok":true,"tracing_enabled":true,"incidents":{"rag_slow":false,"tool_fail":false,"cost_spike":false}}
```

Kết luận: API hoạt động và tracing được bật.

### Public tests

```text
22 passed, 2 warnings in 1.81s
```

Hai warning là cảnh báo deprecation của FastAPI `on_event`; không làm test thất bại.

### Load test — concurrency 1

| Request | Feature | Status | Correlation ID | Latency (ms) |
|---:|---|---:|---|---:|
| 1 | qa | 200 | MISSING | 1411.3 |
| 2 | qa | 200 | MISSING | 8407.2 |
| 3 | summary | 200 | MISSING | 8146.3 |
| 4 | qa | 200 | MISSING | 1429.2 |
| 5 | qa | 200 | MISSING | 1607.3 |
| 6 | summary | 200 | MISSING | 1455.6 |
| 7 | qa | 200 | MISSING | 1420.9 |
| 8 | qa | 200 | MISSING | 1462.1 |
| 9 | qa | 200 | MISSING | 1555.1 |
| 10 | qa | 200 | MISSING | 1303.0 |

Tóm tắt: 10/10 request trả HTTP 200. Phần lớn latency khoảng 1.3–1.6 giây, có hai outlier khoảng 8.1–8.4 giây. Chưa thể nối request với log/trace vì correlation ID bị thiếu.

### Load test — concurrency 5

| Request | Feature | Status | Correlation ID | Latency (ms) |
|---:|---|---:|---|---:|
| 1 | qa | 200 | MISSING | 8352.7 |
| 2 | qa | 200 | MISSING | 8352.0 |
| 3 | qa | 200 | MISSING | 8355.0 |
| 4 | qa | 200 | MISSING | 8352.3 |
| 5 | summary | 200 | MISSING | 8354.0 |
| 6 | qa | 200 | MISSING | 8307.8 |
| 7 | qa | 200 | MISSING | 8309.0 |
| 8 | summary | 200 | MISSING | 8310.3 |
| 9 | qa | 200 | MISSING | 8309.5 |
| 10 | qa | 200 | MISSING | 8308.6 |

Tóm tắt: 10/10 request trả HTTP 200, latency khoảng 8.3 giây/request. Đây là baseline cần so sánh lại sau khi xử lý logging/tracing và xác định nguyên nhân latency.

### Logging validator

```text
Total log records analyzed: 62
Records with missing required fields: 60
Records with missing enrichment (context): 60
Unique correlation IDs found: 0
Potential PII leaks detected: 0
Estimated Score: 30/100
```

Kết luận: PII scrub đạt kiểm tra baseline, nhưng required fields, enrichment và correlation propagation chưa đạt. Ngưỡng `80/100` là mục tiêu của CP1, không phải kết quả baseline CP0.

### Challenge integrity

```text
challenge.json: tracked version unchanged
```

## Các vấn đề chuyển sang checkpoint tiếp theo

1. Correlation ID đang là `MISSING` trong toàn bộ 20 response của load test.
2. Validator không tìm thấy correlation ID nào trong log.
3. 60/62 records thiếu required fields và enrichment.
4. Concurrency 5 có latency khoảng 8.3 giây dù incident flags đều tắt; cần khoanh vùng bằng sub-component spans ở CP2.
5. Cần thu baseline bàn giao từ thành viên A/B/C/D.

## Lệnh tái chạy

Xem `docs/qa-test-plan.md`, mục **Lệnh tái chạy baseline CP0**.
