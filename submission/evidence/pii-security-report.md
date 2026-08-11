# Báo cáo Kiểm duyệt Bảo mật & Che đậy PII (Security & PII Redaction Report)

**Người thực hiện**: Thành viên B — Security Engineer  
**Thành phần phụ trách**: `app/pii.py`, `app/logging_config.py`, `tests/test_pii.py`  
**Trạng thái cuối cùng**: ✅ **100/100 PASSED — 0 PII LEAKS**

---

## 1. Bảng Kiểm Thử Bộc Lộ & Che Đậy PII (Synthetic Test Dataset Results)

| Loại dữ liệu (PII Category) | Dữ liệu đầu vào thô (Raw Input) | Dữ liệu sau khi Redact (Output Log/Trace) | Trạng thái |
|---|---|---|:---:|
| **Email** | `student@vinuni.edu.vn` | `[REDACTED_EMAIL]` | ✅ PASSED |
| **Số điện thoại VN** | `0901234567` / `+84 90 123 4567` | `[REDACTED_PHONE_VN]` | ✅ PASSED |
| **Căn cước công dân (CCCD)** | `001099123456` | `[REDACTED_CCCD]` | ✅ PASSED |
| **Thẻ tín dụng (Credit Card)** | `4111 2222 3333 4444` | `[REDACTED_CREDIT_CARD]` | ✅ PASSED |
| **Hộ chiếu (Passport)** | `B1234567` | `[REDACTED_PASSPORT]` | ✅ PASSED |
| **Địa chỉ Việt Nam** | `Phường Bến Thành, Quận 1, TP. Hồ Chí Minh` | `[REDACTED_ADDRESS_VN]` | ✅ PASSED |
| **Mã định danh (User ID)** | `secret_user_123@domain.com` | `e2a4b8c9d10f` (SHA-256 12-char hex) | ✅ PASSED |

---

## 2. Bằng Chứng Lọc PII Trong Nhật Ký Giao Dịch (Live Request Log Evidence)

### A. Chuỗi tin nhắn gửi từ Client chứa nhiều PII:
> *"Tôi muốn hỏi về chính sách hoàn tiền cho giao dịch với email student@vinuni.edu.vn, SĐT 0901234567, số hộ chiếu B1234567 tại Phường Bến Thành, Quận 1"*

### B. Bản ghi Log JSONL được ghi nhận (Đã xử lý qua `scrub_event` đệ quy):
```json
{
  "service": "api",
  "env": "dev",
  "correlation_id": "req-36f22b57",
  "user_id_hash": "e2a4b8c9d10f",
  "session_id": "k3-challenge-s01",
  "feature": "refund",
  "model": "claude-sonnet-4-5",
  "event": "request_received",
  "level": "info",
  "ts": "2026-08-11T04:20:30.123456Z",
  "payload": {
    "message_preview": "Tôi muốn hỏi về chính sách hoàn tiền cho giao dịch với email [REDACTED_EMAIL], SĐT [REDACTED_PHONE_VN], số hộ chiếu [REDACTED_PASSPORT] tại [REDACTED_ADDRESS_VN]"
  }
}
```

---

## 3. Kiểm Định Tránh Redact Nhầm (False-Positive Protection)

Đã kiểm tra bộ lọc không can thiệp vào các tham số kỹ thuật an toàn:
* **Correlation ID**: `req-36f22b57` ➔ Giữ nguyên 100%.
* **Latency**: `1448ms` ➔ Giữ nguyên 100%.
* **Token Usage**: `tokens_in: 36, tokens_out: 157` ➔ Giữ nguyên 100%.
* **Event Name**: `request_received`, `response_sent` ➔ Giữ nguyên 100%.

---

## 4. Kết Quả Chạy Kiểm Định Tự Động (`scripts/validate_logs.py`)

```text
--- Lab Verification Results ---
Total log records analyzed: 35
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 16
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```

---

## 5. Kết Quả Kiểm Thử Tự Động (`pytest`)

```text
34 passed, 2 warnings in 2.57s
(11/11 tests thuộc module security & PII redaction đạt 100% PASSED)
```

---

## 6. Nội Dung Bàn Giao Cho Thành Viên E Đưa Vào `submission/REPORT.md`

### Mục 3: Logging & Tracing
- **Evidence PII Redaction**: Đã tạo file bằng chứng `submission/evidence/pii-security-report.md`. Toàn bộ dữ liệu PII bao gồm Email, Phone, CCCD, Thẻ tín dụng, Passport, Địa chỉ VN đều được lọc đệ quy bằng `scrub_event` trước khi render và ghi file.

### Mục 7: Đóng góp cá nhân (Member B)
| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| **Thành viên B** *(Security Engineer)* | Xây dựng Regex patterns cho PII (Email, Phone, CCCD, Credit Card, Passport, Address VN), đăng ký bộ lọc đệ quy `scrub_event` trong `structlog`, bảo vệ băm `user_id_hash` và audit không rò rỉ dữ liệu nhạy cảm trên Traces/Logs (đạt điểm PII leak = 0, score 100/100). | PR #6 (`73b7c3f`) | Học được cách xử lý PII đệ quy trên Structlog pipeline, kỹ thuật tránh false-positive trên correlation ID/metrics, và phân tách trách nhiệm mã hóa bảo mật dữ liệu khách hàng. |

---

## 7. Audit Bảo Mật Dữ Liệu Challenge CP3 (`submission/evidence/cp3-challenge-logs.jsonl`)

Đã tiến hành thẩm định độc lập trên file log thực thi chính thức của Challenge do Thành viên C bàn giao:
- **Incident**: `rag_slow` (Tạo độ trễ trên tính năng `refund`).
- **Tổng số log lines**: 12 dòng nhật ký (`request_received` và `response_sent`).
- **Correlation IDs thẩm định**: `req-5f57363a`, `req-33c9924b`, `req-7644f60a`, `req-33bedc14`, `req-84c54330`.
- **Mã hóa User ID**: 100% User ID thô (`k3-u01`..`k3-u05`) đều được băm SHA-256 (`026017618b2c`, `5da42a0d3d01`, `867738e76862`, `026c7a407135`, `b7fde6ae11b0`).
- **Nội dung Previews**: 100% tin nhắn hỏi đáp đều đi qua `summarize_text()`, không lộ dữ liệu nhạy cảm.
- **Kết luận Bảo mật CP3**: **`0 PII Leaks` (Đạt 100% tiêu chí an toàn dữ liệu Challenge)**.

