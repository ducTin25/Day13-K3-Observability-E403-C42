# QA Test Plan — Thành viên E

## Mục tiêu

Kiểm chứng hệ thống có thể chạy ổn định, tạo được evidence cho ba lớp Metrics → Traces → Logs, không làm lộ PII và tách biệt dữ liệu practice với official challenge.

## Phạm vi và quy ước dữ liệu

- **Baseline/Practice:** dùng `data/sample_queries.jsonl` và các scenario được bật rõ bằng `scripts/inject_incident.py --scenario ...`.
- **Official challenge:** chỉ dùng `config/challenge.json` đã được Lab Coach release và tùy chọn `--challenge`.
- Không sửa `config/challenge.json` trong quá trình kiểm thử.
- Evidence không được chứa API key, secret hoặc PII nguyên văn.
- Mỗi lần chạy cần ghi thời gian, concurrency, incident đang bật, status, latency và correlation ID.

## Test matrix

| ID | Trường hợp | Input/điều kiện | Kết quả mong đợi | Evidence cần thu |
|---|---|---|---|---|
| QA-01 | Health check | `GET /health` | HTTP 200, `ok=true`; hiển thị trạng thái tracing và incident | Output health đã sanitize |
| QA-02 | Public tests | Chạy toàn bộ tests | Tất cả tests pass; warning được ghi nhận riêng | Output `pytest -q` |
| QA-03 | Happy path, concurrency 1 | Sample queries, không bật incident | Mỗi request trả HTTP 200; có latency và correlation ID hợp lệ | Output load test và JSON log tương ứng |
| QA-04 | Happy path, concurrency 5 | Cùng workload QA-03, concurrency 5 | Không crash; không lẫn context giữa request; mỗi request có correlation ID riêng | Output load test, assertions/log lines |
| QA-05 | Validation error | Gửi payload thiếu field bắt buộc hoặc sai kiểu | HTTP 422; response không có stack trace/raw input; log có correlation ID nếu request đã qua middleware | Response và JSON log |
| QA-06 | Incoming correlation ID hợp lệ | Gửi request với correlation ID hợp lệ | Header, body, log và trace metadata dùng cùng ID | Response header/body, log line, trace ID |
| QA-07 | Incoming correlation ID không hợp lệ | Gửi ID sai format/quá dài | Hệ thống thay bằng ID hợp lệ mới; không phản chiếu dữ liệu nguy hiểm | Response và log line |
| QA-08 | PII redaction | Payload chứa email, số điện thoại và số thẻ mẫu | Log/trace không chứa PII nguyên văn; chỉ còn placeholder/hash | Assertion, log đã scrub và validator |
| QA-09 | Tool failure practice | Bật scenario `tool_fail`, chạy practice workload | Lỗi được xử lý an toàn; không lộ stack trace/raw input; metrics/trace/log cùng phản ánh failure | Metrics, trace ID và log theo correlation ID |
| QA-10 | Slow RAG practice | Bật scenario `rag_slow`, chạy cùng input/concurrency với baseline | Latency tăng; RAG span chiếm phần lớn chênh lệch | P95 before/after, waterfall và log |
| QA-11 | Cost spike practice | Bật scenario `cost_spike`, chạy cùng input với baseline | Token/cost tăng và xuất hiện đúng trong trace/metrics, không capture raw PII | Trace metadata và số liệu before/after |
| QA-12 | Official challenge | Chỉ sau khi challenge được release; dùng `--challenge --concurrency 5` | Điều tra theo Metrics → Traces → Logs; có root cause, fix và recovery | Challenge ID, metric, trace ID, correlation log, before/after |

## Lệnh tái chạy baseline CP0

Khởi động API ở terminal thứ nhất:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload --env-file .env
```

Chạy kiểm tra ở terminal thứ hai:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\load_test.py --concurrency 1
.\.venv\Scripts\python.exe scripts\load_test.py --concurrency 5
.\.venv\Scripts\python.exe scripts\validate_logs.py
git diff --exit-code -- config/challenge.json
```

## Tiêu chí hoàn thành CP0

- Health check, public tests và load test concurrency 1/5 chạy được.
- Baseline ghi rõ status, latency và tình trạng correlation ID.
- Có output validator ban đầu, kể cả khi chưa đạt ngưỡng CP1.
- Practice và official challenge được phân biệt rõ.
- `config/challenge.json` không bị sửa.
- Baseline từ A/B/C/D được bổ sung vào report/evidence khi từng thành viên bàn giao.

## Phụ thuộc sau CP0

- Thành viên A hoàn thiện correlation ID, middleware và exception handling.
- Thành viên B hoàn thiện PII scrub và test liên quan.
- Thành viên C cung cấp baseline metrics/dashboard.
- Thành viên D cung cấp SLO, alert và runbook baseline.
