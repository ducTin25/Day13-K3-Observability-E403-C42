# Thành viên E — QA & Chief Investigator

## Phạm vi phụ trách

Thành viên E chịu trách nhiệm load test, tracing cho các sub-component RAG/LLM, điều tra challenge theo bằng chứng và tổng hợp báo cáo/evidence của cả nhóm.

## Trạng thái repo hiện tại

- `scripts/load_test.py` hỗ trợ concurrency và challenge mode nhưng chưa lưu kết quả có cấu trúc.
- `LabAgent.run()` đã được observe như generation nhưng RAG `retrieve()` và `FakeLLM.generate()` chưa có span riêng.
- Trace metadata hiện có prompt name/label/version nhưng chưa có correlation ID.
- Challenge K3 đã release, incident là `rag_slow`, feature ảnh hưởng là `refund`, threshold challenge là 2000 ms.
- `submission/REPORT.md` còn là template trống.
- Repo yêu cầu prompt v1/v2 và rollback nhưng phân công 5 thành viên hiện chưa chỉ rõ owner.

## Checkpoint 0 — QA baseline và test plan

### Task

- Chạy health check, public tests, load test concurrency 1 và 5.
- Lưu baseline latency/status/correlation ID mà không chứa PII.
- Lập test matrix cho happy path, validation error, tool failure, slow RAG và cost spike practice.
- Thu baseline output từ A/B/C/D để chuẩn bị report.
- Xác nhận challenge file chỉ được đọc, không bị sửa.

### Acceptance criteria

- Có test plan với input, expected result và evidence cần thu.
- Baseline có thể tái chạy bằng lệnh ghi rõ.
- Tách rõ practice data và official challenge data.

### Blocker/dependency

- Không có blocker cứng cho practice.
- Test end-to-end hoàn chỉnh phụ thuộc A/B sửa logging và PII.

## Checkpoint 1 — QA logging và PII

### Task

- Chạy request có incoming correlation ID hợp lệ/không hợp lệ.
- Chạy nhiều request đồng thời để phát hiện context leakage.
- Kiểm tra body/header/log có cùng ID.
- Chạy payload chứa PII test và xác nhận log chỉ còn placeholder/hash.
- Kiểm tra exception response không lộ stack trace hoặc raw input.
- Chạy `validate_logs.py` sau khi tạo lượt log sạch.

### Acceptance criteria

- Có evidence correlation propagation và PII redaction.
- Validator đạt ít nhất 80/100, mục tiêu 100/100.
- Không có test chỉ dựa vào screenshot; phải có log line hoặc assertion kiểm chứng được.

### Blocker/dependency

- Phụ thuộc A hoàn thiện middleware/exception handler.
- Phụ thuộc B bật scrub processor và hoàn thiện tests.

## Checkpoint 2 — Trace RAG/LLM, prompt version và evidence

### Task E1 — Tạo span cho sub-components

- Tạo span/observation riêng cho RAG retrieve.
- Tạo generation/span riêng cho LLM generate với model, token usage, cost và latency phù hợp.
- Giữ `capture_input=False`, `capture_output=False` hoặc chỉ gửi dữ liệu đã sanitize.
- Bảo đảm waterfall thể hiện được agent → RAG → LLM.
- Gắn correlation ID vào trace metadata để nối trace với JSON log.
- Thêm test adapter/mocking để không cần gọi Langfuse thật trong unit test.

### Task E2 — Prompt versioning đang thiếu owner

Phân công hiện tại chưa giao prompt versioning cho ai. Đề xuất E nhận vì E sở hữu trace/evidence:

- Tạo prompt `day13-chat` v1/v2 theo `docs/PROMPT_VERSIONING.md`.
- Gán baseline/candidate hoặc production label theo hướng dẫn.
- Chạy cùng input với hai version/label.
- Chứng minh trace có `prompt_name`, `prompt_label`, `prompt_version` thật.
- Thực hiện một lần đổi label hoặc rollback và lưu evidence.
- Không sửa code để giả metadata/version.

Nếu nhóm giao phần này cho người khác, E vẫn phải thu trace IDs và evidence vào report.

### Task E3 — Load test và trace verification

- Tạo tối thiểu 10 traces có metadata.
- Chạy baseline và practice `rag_slow` với cùng input/concurrency.
- Xác nhận trace chậm có RAG span chiếm phần lớn latency.
- Từ trace lấy correlation ID rồi tìm đúng log line.
- Kiểm tra trace không capture raw PII.

### Acceptance criteria

- Có tối thiểu 10 traces.
- Có một waterfall agent → RAG → LLM.
- Có hai prompt version/label và evidence rollback/change label.
- Mỗi trace điều tra được nối với log bằng correlation ID.

### Blocker/dependency

- Cần A cung cấp correlation ID trong context hoặc qua tham số.
- Cần B xác nhận metadata/preview gửi Langfuse đã sanitize.
- Cần Langfuse host/key hoạt động thực; `.env` đã có biến nhưng vẫn phải kiểm tra kết nối.
- Prompt versioning là blocker điểm nhóm nếu không chốt owner.

## Checkpoint 3 — Chief Investigator

### Task E1 — Chạy official challenge

- Chỉ dùng `config/challenge.json` đã release.
- Bật incident bằng `python scripts/inject_incident.py`.
- Chạy `python scripts/load_test.py --challenge --concurrency 5`.
- Ghi challenge ID, thời gian chạy và affected feature.

### Task E2 — Điều tra theo bằng chứng

Thực hiện đúng thứ tự:

1. Metrics: xác định triệu chứng, time window và độ lệch so với baseline/SLO.
2. Traces: chọn trace bất thường, so sánh thời gian từng span.
3. Logs: dùng correlation ID tìm log line cùng request.
4. Root cause: chỉ kết luận khi ba lớp evidence khớp.
5. Đề xuất fix action, mitigation và preventive measure.

Với challenge hiện tại, giả thuyết cần kiểm chứng là RAG latency tăng trên feature `refund`; không dùng nội dung source làm bằng chứng thay cho metrics/trace/log runtime.

### Task E3 — Recovery verification

- Disable incident sau khi thu evidence.
- Chạy lại cùng workload.
- Xác nhận P95/span RAG trở lại baseline hoặc dưới threshold.
- Lưu before/after có cùng điều kiện test.

### Acceptance criteria

- Kết luận có metric cụ thể, trace ID và log/correlation ID.
- Có fix action và preventive measure hợp lý.
- Có evidence recovery, không chỉ evidence sự cố.

### Blocker/dependency

- Challenge đã release, không còn blocker từ Lab Coach.
- Phụ thuộc C cung cấp dashboard/time window, A cung cấp correlation log và D cung cấp SLO/runbook.
- Nếu sub-component spans chưa hoàn thành, không thể chứng minh RAG là span bất thường.

## Hoàn tất — Báo cáo và demo

### Task

- Hoàn thiện tất cả mục trong `submission/REPORT.md`.
- Thu commit/PR và mô tả đóng góp từ A–D.
- Đặt evidence trong `submission/evidence/` và dẫn link tương đối trong report.
- Kiểm tra evidence tối thiểu: validator log, 10 traces, waterfall, prompt v1/v2, rollback, correlation log, PII redaction, dashboard 6 panel, alerts/runbook và challenge.
- Chạy full tests và các validator cuối.
- Kiểm tra Git không chứa `.env`, secret, raw PII hoặc log nhạy cảm.
- Chuẩn bị demo Metrics → Traces → Logs → Root cause → Recovery.

### Acceptance criteria

- Report khớp commit history và evidence thật.
- Mỗi thành viên có phần đóng góp cá nhân và commit/PR cụ thể.
- Demo có thể tái hiện bằng các lệnh đã ghi.

## Thứ tự thực hiện đề xuất

1. Lập QA matrix và baseline.
2. Verify CP1 của A/B.
3. Thêm RAG/LLM spans và correlation metadata.
4. Chốt owner và hoàn thành prompt versioning.
5. Thu dashboard/SLO/alert evidence từ C/D.
6. Chạy official challenge và recovery test.
7. Hoàn thiện report, evidence và demo.
