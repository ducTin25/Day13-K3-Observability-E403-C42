# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 30/100 (Baseline CP0) ➔ 100/100 (Sau CP3 Challenge)
- Tổng số traces:
- Số PII leak còn lại: 0 (Đã kiểm định 100% không còn PII leak)
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction: submission/evidence/pii-security-report.md
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| **Thành viên B** *(Security Engineer)* | Xây dựng Regex PII patterns (Email, Phone, CCCD, Card, Passport, Address VN), lọc đệ quy `scrub_event` trong `structlog`, băm `user_id_hash` và audit không lộ dữ liệu nhạy cảm trên Log/Trace (0 Leak, Score 100/100). | PR #6 (`73b7c3f`) | Kỹ thuật PII scrubbing đệ quy trong Structlog, bảo vệ dữ liệu nhạy cảm trước khi ghi log/trace và loại trừ false-positive trên correlation IDs. |
| | | | |
