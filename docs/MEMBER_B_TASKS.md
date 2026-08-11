# Thành viên B — Security Engineer

## Phạm vi phụ trách

Thành viên B chịu trách nhiệm PII scrubbing, regex patterns, kiểm tra log không lộ dữ liệu nhạy cảm và cung cấp evidence bảo mật cho báo cáo.

## Trạng thái repo hiện tại

- `app/pii.py` đã có email, số điện thoại Việt Nam, CCCD và thẻ tín dụng.
- TODO yêu cầu bổ sung pattern như passport và từ khóa địa chỉ Việt Nam.
- `scrub_event` đã tồn tại nhưng chưa được đăng ký trong pipeline ở `app/logging_config.py`.
- `scrub_event` hiện chủ yếu xử lý string trong `payload` và `event`, chưa scrub đệ quy toàn bộ cấu trúc.
- Tests mới kiểm tra email và một số định dạng số điện thoại.
- Validator hiện báo 0 PII leak trên log cũ, nhưng điều này chưa chứng minh pipeline scrub hoạt động với request mới.

## Checkpoint 0 — Threat model và baseline

### Task

- Liệt kê nơi PII có thể đi vào hệ thống: `message`, `user_id`, `session_id`, exception detail, prompt/answer preview và nested payload.
- Chạy test PII hiện có và lưu baseline validator.
- Chuẩn bị bộ dữ liệu giả gồm email, phone, CCCD, thẻ test, passport và địa chỉ.
- Chỉ dùng dữ liệu test, không dùng PII thật.

### Acceptance criteria

- Có danh sách field/risk và bộ input kiểm thử tái sử dụng được.
- Baseline không chứa secret hoặc PII thật.

### Blocker/dependency

- Không có blocker cứng.
- Việc kiểm chứng end-to-end cần API của A chạy và tạo log mới.

## Checkpoint 1 — PII scrubbing

### Task B1 — Hoàn thiện patterns

- Rà soát regex email và phone để tránh bỏ sót định dạng phổ biến.
- Giữ coverage cho CCCD 12 chữ số và thẻ 16 chữ số có khoảng trắng/dấu gạch.
- Bổ sung passport theo format được nhóm thống nhất.
- Bổ sung từ khóa/định dạng địa chỉ Việt Nam một cách thận trọng.
- Tránh regex quá rộng làm redact nhầm latency, token, trace ID hoặc correlation ID.

### Task B2 — Scrub trước khi ghi log

- Đăng ký `scrub_event` trước `JsonlFileProcessor` và trước JSON renderer.
- Scrub đệ quy string trong dict/list/tuple nếu log có nested payload.
- Kiểm tra cả top-level dynamic fields, không chỉ `payload`.
- Không biến đổi các field kỹ thuật an toàn như event name nếu không cần thiết.
- Bảo đảm raw `user_id` không được log; A phải dùng `hash_user_id()`.

### Task B3 — Tests và negative tests

- Test từng PII type độc lập.
- Test nhiều PII type trong cùng một string.
- Test PII nằm trong nested payload và exception detail.
- Test input có xuống dòng hoặc dấu câu.
- Test false positive với correlation ID, latency, token count và số không phải PII.
- Test trực tiếp file JSONL sau một request API, không chỉ test `scrub_text()`.
- Chạy `scripts/validate_logs.py` và kiểm tra `Potential PII leaks detected: 0`.

### Acceptance criteria

- Không còn email, phone, CCCD hoặc thẻ test nguyên văn trong log.
- Placeholder thể hiện được loại dữ liệu, ví dụ `[REDACTED_EMAIL]`.
- Scrubbing xảy ra trước khi dữ liệu được render và ghi file.
- Tests chứng minh vừa không leak vừa hạn chế redact nhầm.

### Blocker/dependency

- Phụ thuộc A bind metadata đúng và không log raw `user_id`.
- Exception handler của A không được bypass structlog processor.
- Pattern passport/address cần team thống nhất phạm vi để tránh false positive lớn.

## Checkpoint 2 — Kiểm chứng trace và dashboard không lộ PII

### Task

- Kiểm tra log dùng làm nguồn dashboard không chứa raw PII.
- Phối hợp E kiểm tra metadata/input/output gửi lên Langfuse; không giả định log scrubber tự bảo vệ trace.
- Kiểm tra `query_preview`, `message_preview`, `answer_preview` đều đi qua hàm tóm tắt/scrub.
- Kiểm tra screenshot/evidence không vô tình hiển thị key, email hay dữ liệu người dùng.
- Bàn giao cho C một file log sạch để dựng dashboard.

### Acceptance criteria

- Log local, trace metadata và evidence đều dùng dữ liệu đã sanitize/hash.
- Dashboard chỉ hiển thị metrics tổng hợp, không hiển thị PII thô.

### Blocker/dependency

- Langfuse trace capture phụ thuộc E; E cần để `capture_input=False`, `capture_output=False` hoặc scrub dữ liệu trước khi gửi.
- Evidence runtime phụ thuộc C/E tạo dashboard và trace.

## Checkpoint 3 — Challenge

### Task

- Kiểm tra log challenge trước khi đưa vào report.
- Xác nhận các correlation ID/log line được E trích dẫn không chứa PII.
- Nếu exception chứa input người dùng, xác minh scrubber che dữ liệu trước khi ghi.
- Ghi nhận PII leak count cuối cùng.

### Blocker/dependency

- Challenge đã release.
- Phụ thuộc A/E tạo log và trace challenge thật.

## Hoàn tất và bàn giao

- Commit/PR cho patterns, recursive scrubber và tests.
- Bảng test case: input giả, expected placeholder, kết quả.
- Output validator với 0 PII leak.
- Evidence một request chứa nhiều PII nhưng log chỉ còn placeholder.
- Xác nhận Git không chứa `.env`, secret hoặc raw PII.
- Ghi phần đóng góp cá nhân và commit SHA vào `submission/REPORT.md`.

## Thứ tự thực hiện đề xuất

1. Threat model và test cases.
2. Hoàn thiện patterns.
3. Hoàn thiện/đăng ký scrub processor.
4. Unit tests và false-positive tests.
5. End-to-end test cùng A.
6. Audit trace/evidence cùng E.
