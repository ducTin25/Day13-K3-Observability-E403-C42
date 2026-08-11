# Thành viên A — API & Middleware

## Phạm vi phụ trách

Thành viên A chịu trách nhiệm correlation ID xuyên suốt request, request metadata cho structured log và exception handler mở rộng. A là đầu mối cung cấp khóa liên kết từ API log sang trace và dashboard.

## Trạng thái repo hiện tại

- `app/middleware.py` còn TODO cho toàn bộ vòng đời correlation ID.
- `app/main.py` chưa bind `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- `/chat` chỉ có `try/except` cục bộ; chưa có exception handler thống nhất.
- `validate_logs.py` hiện đạt 30/100: không có correlation ID hợp lệ và phần lớn API log thiếu metadata.
- Public tests đang pass nhưng chưa kiểm tra đầy đủ middleware, response header và lỗi.

## Checkpoint 0 — Setup và baseline

### Task

- Kích hoạt đúng `.venv`; không dùng Python hệ thống.
- Chạy API, kiểm tra `/health`, `/chat`, response headers và `data/logs.jsonl`.
- Chạy load test và lưu baseline `validate_logs.py` cho thành viên E.
- Ghi nhận baseline hiện tại 30/100 trước khi sửa.

### Acceptance criteria

- API chạy được bằng môi trường của repo.
- Có kết quả baseline có thời gian chạy và lệnh sử dụng.
- Không ghi `.env`, secret hoặc raw PII vào evidence.

### Blocker/dependency

- Không có blocker cứng.
- Log cũ có nhiều record không hợp lệ. Cần lưu bằng chứng baseline rồi tạo lượt log sạch; chỉ append log mới sẽ khiến validator tiếp tục fail.

## Checkpoint 1 — Middleware, metadata và exception handler

### Task A1 — Hoàn thiện `CorrelationIdMiddleware`

- Gọi `clear_contextvars()` ở đầu request để tránh rò context giữa các request.
- Đọc `x-request-id`; chỉ giữ ID đúng dạng `req-<8 ký tự hex>`.
- Sinh ID mới bằng UUID khi header thiếu hoặc không hợp lệ.
- Bind `correlation_id` vào structlog contextvars.
- Gán ID vào `request.state.correlation_id`.
- Đo tổng thời gian xử lý bằng `time.perf_counter()`.
- Trả `x-request-id` và `x-response-time-ms` trong response.
- Dọn context an toàn cả khi request thành công hoặc phát sinh lỗi.

### Task A2 — Bind request metadata

Trước log `request_received`, bind:

- `user_id_hash=hash_user_id(body.user_id)`; không log raw `user_id`.
- `session_id=body.session_id`.
- `feature=body.feature`.
- `model=agent.model`.
- `env=APP_ENV`, mặc định `dev`.

Các event `request_received`, `response_sent` và `request_failed` của cùng request phải nhận cùng context.

### Task A3 — Exception handler mở rộng

- Xử lý thống nhất `HTTPException`, validation error cần quan sát và exception không dự kiến.
- Response lỗi phải có correlation ID và `x-request-id`.
- Ghi `request_failed` với `error_type`, status code, path/method cần thiết.
- Gọi `record_error()` đúng một lần cho mỗi lỗi được tính.
- Không trả stack trace, raw exception hoặc dữ liệu nhạy cảm cho client.
- Refactor `try/except` hiện tại trong `/chat` để tránh log và đếm lỗi hai lần.

### Task A4 — Tests

- Test sinh ID mới và giữ incoming ID hợp lệ.
- Test thay incoming ID sai format.
- Test body, header và log có cùng correlation ID.
- Test hai request liên tiếp/đồng thời không dùng chung context.
- Test response lỗi vẫn có correlation ID.
- Test một exception chỉ làm tăng error counter một lần.
- Test raw `user_id` không xuất hiện trong log.

### Acceptance criteria

- Mọi API log có correlation ID hợp lệ.
- API log có đủ `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- `validate_logs.py` đạt tối thiểu 80/100; mục tiêu 100/100.
- Toàn bộ test pass bằng `.venv\Scripts\python.exe -m pytest -q`.

### Blocker/dependency

- Phụ thuộc B bật PII scrubber trước bước render/write log.
- Phải thống nhất với C mẫu số của `error_rate_pct`. Validation error không được tạo `request_failed` mà thiếu event tương ứng trong mẫu số.

## Checkpoint 2 — Tích hợp metrics, traces và dashboard

### Task

- Bàn giao contract của `request_received`, `response_sent`, `request_failed` cho C.
- Bảo đảm lỗi có `error_type` ổn định để C breakdown.
- Cung cấp correlation ID cho E để gắn vào metadata của trace.
- Chạy load test tạo log hợp lệ cho dashboard và ít nhất 10 request/trace.
- Kiểm tra từ một correlation ID có thể tìm đúng response log và trace liên quan.

### Acceptance criteria

- C tính được error rate từ event do A phát ra.
- E có thể nối trace với log bằng correlation ID.
- Log đầu vào dashboard không thiếu các field thuộc phạm vi A.

### Blocker/dependency

- `app/agent.py` hiện chưa gắn correlation ID vào Langfuse trace; A và E phải thống nhất truyền tham số hoặc đọc từ contextvars.
- Dashboard runtime phụ thuộc C và PII-safe log phụ thuộc B.

## Checkpoint 3 — Challenge

### Task

- Không sửa `config/challenge.json`.
- Cung cấp correlation ID, response headers và log line của request bất thường cho E.
- Hỗ trợ chứng minh chuỗi metric → trace → correlation ID → log.
- Nếu có lỗi, kiểm tra exception response không lộ nội bộ hoặc PII.

### Blocker/dependency

- Challenge đã release, không còn blocker từ Lab Coach.
- Điều tra đầy đủ vẫn phụ thuộc E tạo span RAG/LLM có correlation ID.

## Hoàn tất và bàn giao

- Commit/PR riêng cho middleware, metadata, exception handler và tests.
- Kết quả cuối của `validate_logs.py`.
- Evidence body/header/log cùng correlation ID.
- Evidence exception response an toàn.
- Ghi phần đóng góp cá nhân và commit SHA vào `submission/REPORT.md`.

## Thứ tự thực hiện đề xuất

1. Middleware.
2. Bind metadata.
3. Exception handler.
4. Unit/integration tests.
5. Phối hợp B về scrubber.
6. Regenerate log và chạy validator.
7. Bàn giao contract cho C/E.
