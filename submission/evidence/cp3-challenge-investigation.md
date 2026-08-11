# CP3 — Điều tra Challenge chính thức (Thành viên D)

## Bối cảnh

- Challenge ID: `day13-k3-observability-v1`, cohort K3, incident khai báo: `rag_slow`, affected feature: `refund`, `latency_threshold_ms: 2000`.
- Chạy theo đúng luồng README: `python scripts/inject_incident.py` rồi `python scripts/load_test.py --challenge --concurrency 5`.
- Điều tra dựa trên alert/runbook đã viết ở CP2 (`config/alert_rules.yaml`, `docs/alerts.md`), không đọc trước `app/incidents.py`/`app/mock_rag.py` trước khi xem triệu chứng qua metrics.

## Bước 1 — Metrics (phát hiện triệu chứng)

Snapshot `GET /metrics` trước incident (traffic=0, sau khi restart server sạch):

```json
{"traffic":0,"latency_p95":0.0, ...}
```

Snapshot sau khi chạy 5 query challenge (feature `refund`):

```json
{"traffic":5,"latency_p50":4194.0,"latency_p95":6153.0,"latency_p99":6153.0,"error_rate_pct":0.0,"quality_avg":0.86,"total_cost_usd":0.0088}
```

→ Khớp **Alert 1 — Chat API Latency P95 Breach** (`docs/alerts.md#alert-1`): P95 6153ms > ngưỡng 3000ms (`config/slo.yaml: latency_p95_ms.critical_threshold`). Cả 5/5 request đều vượt threshold (100% breach rate trong batch).
→ **Alert 2 (error rate)**, **Alert 3 (quality)**, **Alert 4 (cost)** đều không trigger: error_rate_pct=0%, quality_avg=0.86 (>0.75), cost=0.0088 USD (<<2.5 USD).

- Severity: **Critical** (đúng severity đã gán cho Alert 1).
- Impacted SLO: `latency_p95_ms` (`config/slo.yaml`).
- Time window: `2026-08-11T05:14:30Z` → `2026-08-11T05:14:53Z` (23 giây, 5 request tuần tự do concurrency thực tế bị giới hạn bởi mock LLM đồng bộ).
- User impact: toàn bộ 5 truy vấn về chính sách hoàn tiền (`refund`) đều phản hồi chậm 3.8–6.15 giây thay vì mức nền ~150ms trước đó — trải nghiệm chờ đợi rõ rệt, dù không có request nào lỗi cứng (0 request thất bại).

## Bước 2 — Traces (khoanh vùng span)

Không truy vấn được Langfuse Read API từ môi trường này (lỗi `401 Unauthorized` khi gọi `client.api.trace.list`, dù ingestion vẫn hoạt động — `tracing_enabled: true`). Khoanh vùng span dựa trên cấu trúc trace đã biết từ `app/agent.py` (`agent.run → rag.retrieve`, `agent.run → llm.generate`) đối chiếu thời gian trong log ở Bước 3 để suy ra span nào chiếm phần lớn latency.

**Khuyến nghị bàn giao cho E/A**: mở Langfuse UI, lọc theo tag `refund` hoặc khoảng thời gian `05:14:30–05:14:53Z`, lấy trace ID gắn với các `correlation_id` liệt kê ở Bước 3 để có bằng chứng waterfall span trực quan (giống cách E đã làm ở CP2 cho practice incident, xem `evidence/cp2-tracing-evidence.md`).

## Bước 3 — Logs (chứng minh root cause)

5 dòng `response_sent` trong `data/logs.jsonl` (khung thời gian challenge):

| correlation_id | feature | latency_ms | tokens_in/out | quality |
|---|---|---|---|---|
| req-933d8fb6 | refund | 6153 | 31/151 | 0.9 |
| req-140f2201 | refund | 3800 | 34/86 | 0.8 |
| req-a0aa5316 | refund | 4053 | 29/132 | 0.9 |
| req-8f4be8c3 | refund | 4223 | 34/87 | 0.8 |
| req-13e9d431 | refund | 4194 | 34/97 | 0.9 |

Token count thấp và bình thường (tương đương baseline ~30/100) — loại trừ giả thuyết "LLM sinh output dài hơn gây chậm". Latency tăng không tương quan với token count → nghi vấn dồn về bước trước LLM, tức `rag.retrieve`.

Đọc trực tiếp `app/mock_rag.py:17-18` để xác nhận (chỉ đọc sau khi đã có giả thuyết từ metrics/log, không kết luận trước):

```python
if STATE["rag_slow"]:
    time.sleep(2.5)
```

## Root cause

`rag.retrieve()` chèn `time.sleep(2.5)` khi incident `rag_slow` bật — cộng với latency nền (~1–1.2s sau khi bật tracing thật, xem phần "Phát hiện phụ" bên dưới) ra đúng khoảng 3.8–6.15s quan sát được. Đây **không phải lỗi riêng của feature `refund`** — `mock_rag.retrieve()` chèn delay cho **mọi** message, không lọc theo feature; do 5 câu hỏi trong `config/challenge.json` đều gắn `feature: refund` nên triệu chứng biểu hiện tập trung ở feature này, nhưng về bản chất đây là sự cố ở tầng RAG toàn cục.

## Mitigation đã áp dụng và xác minh recovery

- Hành động: `POST /incidents/rag_slow/disable` (tương đương "tắt incident" — mitigation hợp lệ theo runbook Alert 1, không cần rollback code).
- Xác minh: chạy lại `python scripts/load_test.py` (10 request bình thường) sau khi tắt.
- Kết quả latency 10 request ngay sau khi tắt (tính riêng, không lẫn với batch incident cũ vì `/metrics` là cộng dồn từ lúc start process — xem phát hiện phụ bên dưới):

```
n=10, values=[1069, 1076, 1084, 1100, 1105, 1122, 1123, 1176, 1179, 1200] ms
p95=1200ms, p50=1122ms
```

→ **P95 = 1200ms < 3000ms (objective)** — SLO latency đã phục hồi, điều kiện đóng incident theo `docs/alerts.md#alert-1` được thoả (recovery liên tục, không phải 1 điểm dữ liệu đơn lẻ — đã lấy đủ 10 mẫu).
- error_rate_pct vẫn 0%, không phát sinh lỗi trong lúc mitigation.

## Phát hiện phụ (đáng ghi vào report, không phải root cause của challenge)

Sau khi bật Langfuse key thật (`tracing_enabled: true`), latency nền của request bình thường (không incident) tăng từ ~150ms (khi tracing tắt, dùng local fallback) lên ~1070–1200ms. Nguyên nhân nghi ngờ: `app/prompt_management.py:43` gọi `client.get_prompt(...)` — một network call thật tới Langfuse Cloud — đồng bộ trong mỗi request thay vì chỉ khi cache miss. Đây là **overhead do bật observability, không phải do incident `rag_slow`**, nhưng đáng lưu ý vì nó làm dịch chuyển baseline latency và có thể ăn bớt margin của SLO 3000ms trong môi trường production thật. Preventive measure liên quan: cân nhắc fetch prompt bất đồng bộ hoặc tăng `cache_ttl_seconds`/pre-warm cache ở startup thay vì fetch theo từng request.

Ghi chú kỹ thuật khác: endpoint `/metrics` cộng dồn `REQUEST_LATENCIES` từ lúc process khởi động (`app/metrics.py`), không có cửa sổ thời gian trượt — sau incident, `latency_p95` trả về từ `/metrics` vẫn giữ giá trị cũ (6153ms) dù traffic mới đã hồi phục, vì mẫu cũ chưa bao giờ bị loại khỏi danh sách. Phải tính lại P95 thủ công trên các dòng log *sau* thời điểm `incident_disabled` để có con số recovery đúng (đã làm ở trên). Đây là preventive measure cho C/A: cân nhắc windowed metrics (vd: chỉ giữ N phút gần nhất) thay vì cộng dồn vô hạn, nếu không alert "P95 breach" có thể không bao giờ tự hết dù hệ thống đã phục hồi thật.

## Bàn giao cho E (preventive measures đưa vào report)

1. **Prompt fetch đồng bộ mỗi request** — chuyển sang fetch bất đồng bộ hoặc pre-warm cache ở startup để tránh network call chặn mỗi request (ảnh hưởng latency baseline, không riêng incident).
2. **`/metrics` không có time window** — nên giới hạn cửa sổ trượt (vd 5–15 phút) để P95/P99 phản ánh đúng trạng thái hiện tại, tránh alert "treo" mãi sau khi đã fix.
3. **`rag_slow` không lọc theo feature** — nếu muốn incident chỉ ảnh hưởng `refund` như challenge mô tả, `mock_rag.retrieve()` cần điều kiện theo feature; hiện tại là toàn cục, nên trong production một fix tương tự (retry/circuit breaker cho RAG) nên áp dụng toàn hệ thống chứ không giới hạn một feature.
