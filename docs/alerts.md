# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

Lưu ý chung: repo không có alert engine thật. Các bước "kiểm tra" dưới đây thao tác trên `GET /metrics`, dashboard dựng từ `data/logs.jsonl` (xem `config/dashboard.yaml`), và trace trên Langfuse (nếu đã cấu hình `LANGFUSE_*`). Nếu chưa có Langfuse key, thay bước Traces bằng lọc log theo `correlation_id`.

## Alert 1

- Tên: Chat API Latency P95 Breach
- Severity: Critical
- SLI/SLO liên quan: `latency_p95_ms` (`config/slo.yaml`) — objective P95 ≤ 3000ms, warning threshold 2400ms
- Điều kiện và thời gian duy trì: P95 latency của `response_sent` (cửa sổ trượt 5 phút) > 3000ms, duy trì liên tục ≥5 phút hoặc ≥3 lần đánh giá liên tiếp (đánh giá mỗi 60s) để tránh bắn alert vì một request đơn lẻ chậm bất thường
- Ảnh hưởng tới người dùng: người dùng chờ phản hồi lâu bất thường, có thể timeout ở phía client hoặc bỏ dở phiên chat; ảnh hưởng nặng nhất ở feature đang breach (kiểm tra breakdown theo `feature` để biết phạm vi)
- Ba bước kiểm tra đầu tiên (Metrics → Traces → Logs):
  1. **Metrics**: gọi `GET /metrics` hoặc xem panel `latency` trên dashboard — xác nhận `latency_p95`/`latency_p99` đang vượt ngưỡng và từ khi nào; so P95 với P50 để biết là toàn bộ traffic chậm hay chỉ tail bị kéo dài.
  2. **Traces**: mở Langfuse, lọc trace theo khoảng thời gian breach, sort theo duration giảm dần; xác định span nào (retrieval/tool-call/LLM call) chiếm phần lớn thời gian trong các trace chậm nhất.
  3. **Logs**: lấy `correlation_id` của các trace chậm, tìm trong `data/logs.jsonl` các dòng `request_received`/`response_sent` tương ứng để đối chiếu `feature`, `tokens_in/out`, `payload` — xác nhận span chậm ở bước nào khớp với field nào trong log.
- Mitigation tạm thời: nếu breach tập trung ở một feature cụ thể, có thể tạm thời route feature đó sang fallback nhanh hơn (hoặc tắt qua `POST /incidents/{name}/disable` nếu breach do incident đang bật) trong lúc điều tra; rollback bằng cách bật lại `/incidents/{name}/enable` hoặc trả traffic về route gốc sau khi fix.
- Owner: A (API & Middleware) — chịu trách nhiệm đầu tiên vì latency sinh ra từ tầng request/middleware/agent.
- Escalation/owner: nếu không xác định được nguyên nhân trong 15 phút hoặc P95 > 2x objective (>6000ms), escalate cho E (Chief Investigator) để dẫn dắt điều tra toàn nhóm.
- Điều kiện đóng incident: P95 latency quay lại ≤3000ms liên tục trong ≥10 phút và nguyên nhân gốc đã được xác định (không chỉ tự hồi phục không rõ lý do).
- Cách xác minh recovery: theo dõi panel `latency` thêm ít nhất 10 phút sau mitigation, xác nhận P95/P99 ổn định dưới ngưỡng qua nhiều lần đánh giá liên tiếp, không chỉ 1 điểm dữ liệu.

## Alert 2

- Tên: Chat API High Error Rate
- Severity: Critical
- SLI/SLO liên quan: `error_rate_pct` (`config/slo.yaml`) — objective ≤2%, warning threshold 1%
- Điều kiện và thời gian duy trì: `count(request_failed) / count(request_received) * 100` trên cửa sổ trượt 5 phút > 2%, duy trì liên tục ≥5 phút, yêu cầu tối thiểu 5 request trong cửa sổ để tránh alert trên mẫu quá nhỏ
- Ảnh hưởng tới người dùng: một tỉ lệ đáng kể request nhận lỗi 5xx thay vì câu trả lời — người dùng thấy tính năng chat không hoạt động hoặc hoạt động chập chờn
- Ba bước kiểm tra đầu tiên (Metrics → Traces → Logs):
  1. **Metrics**: xem panel `errors` (error rate + breakdown theo `error_type`) hoặc `GET /metrics` field `error_breakdown` — xác định loại lỗi nào chiếm đa số.
  2. **Traces**: trong Langfuse, lọc trace có status lỗi trong khoảng thời gian breach — xác định span nào raise exception (agent, tool call, hay tầng API).
  3. **Logs**: tìm các dòng `event: request_failed` trong `data/logs.jsonl`, đọc `error_type` và `payload.path`/`payload.method` để xác nhận lỗi tập trung ở endpoint/feature nào, đối chiếu `correlation_id` với trace ở bước 2.
- Mitigation tạm thời: nếu lỗi tập trung ở một feature/tool cụ thể, tạm thời trả lỗi mềm (graceful degradation) hoặc tắt tính năng đó qua endpoint incident control nếu có; rollback bằng cách bật lại tính năng sau khi fix và xác nhận error rate ổn định.
- Owner: C (Metrics & Dashboard) — chủ sở hữu định nghĩa và đo đếm `error_rate_pct`; phối hợp A nếu nguyên nhân nằm ở middleware/exception handling.
- Escalation/owner: nếu error rate > 10% hoặc kéo dài quá 15 phút không rõ nguyên nhân, escalate cho E để dẫn dắt điều tra và thông báo toàn nhóm.
- Điều kiện đóng incident: error rate quay lại ≤2% liên tục trong ≥10 phút và root cause đã xác định (không chỉ tự hết lỗi).
- Cách xác minh recovery: theo dõi `error_breakdown` thêm ít nhất 10 phút, xác nhận không phát sinh `error_type` liên quan đến nguyên nhân đã fix.

## Alert 3

- Tên: Response Quality Degradation
- Severity: Warning
- SLI/SLO liên quan: `quality_score_avg` (`config/slo.yaml`) — objective ≥0.75
- Điều kiện và thời gian duy trì: `mean(quality_score)` trên cửa sổ trượt 15 phút < 0.75, duy trì liên tục ≥15 phút (quality là tín hiệu biến thiên chậm hơn latency/error nên cần cửa sổ dài hơn để tránh phản ứng thái quá với 1-2 câu trả lời kém đơn lẻ)
- Ảnh hưởng tới người dùng: câu trả lời có xu hướng kém chính xác/hữu ích hơn bình thường — rủi ro âm thầm hơn lỗi cứng vì không có mã lỗi rõ ràng, người dùng vẫn nhận được response nhưng chất lượng thấp
- Ba bước kiểm tra đầu tiên (Metrics → Traces → Logs):
  1. **Metrics**: xem panel `quality` (`mean(quality_score)`) — xác định thời điểm bắt đầu giảm và mức giảm so với baseline.
  2. **Traces**: mở vài trace trong khoảng breach, xem input/output thực tế và metadata `prompt_name`/`prompt_label`/`prompt_version` — kiểm tra có phải mới đổi prompt version/label hoặc rollback gần đây không.
  3. **Logs**: đối chiếu `feature`/`model` trong `data/logs.jsonl` của các request có `quality_score` thấp — xác định quality giảm ở một feature/model cụ thể hay toàn bộ.
- Mitigation tạm thời: nếu nguyên nhân là một prompt label mới, rollback label về phiên bản trước đó đã biết là ổn định (xem `docs/PROMPT_VERSIONING.md`); nếu do một feature/model cụ thể, có thể tạm route feature đó sang model/prompt dự phòng.
- Owner: E (QA & Chief Investigator) — chủ sở hữu tự nhiên của tín hiệu chất lượng, người điều tra và đánh giá output.
- Escalation/owner: nếu quality trung bình < 0.5 hoặc kéo dài >30 phút không rõ nguyên nhân, escalate cho A/C để kiểm tra tầng hạ tầng (model/tool có đang lỗi ngầm không).
- Điều kiện đóng incident: quality trung bình quay lại ≥0.75 liên tục trong ≥15 phút sau khi đã xác định và áp dụng fix (không chỉ dao động ngẫu nhiên hồi phục).
- Cách xác minh recovery: theo dõi panel `quality` thêm ít nhất 15 phút, xác nhận không có đợt giảm mới sau mitigation; đối chiếu với `prompt_label` hiện tại để chắc chắn đang dùng đúng phiên bản đã rollback.

## Alert 4

- Tên: Daily Cost Budget Risk
- Severity: Warning
- SLI/SLO liên quan: `daily_cost_usd` (`config/slo.yaml`) — objective ≤2.5 USD (trong khoảng đánh giá của phiên lab, xem `window_note`)
- Điều kiện và thời gian duy trì: `sum(cost_usd)` tích luỹ trong khoảng đánh giá > 2.5 USD; đây là giá trị tích luỹ nên không cần "sustain window" — kiểm tra tại mỗi lần snapshot, một lần vượt là đủ để cảnh báo (khác với latency/error là chỉ số tức thời có thể dao động)
- Ảnh hưởng tới người dùng: không ảnh hưởng trực tiếp UX ngay lập tức, nhưng là rủi ro vận hành — chi phí vượt ngân sách có thể dẫn tới việc phải giới hạn traffic/tắt tính năng đột ngột nếu không xử lý kịp
- Ba bước kiểm tra đầu tiên (Metrics → Traces → Logs):
  1. **Metrics**: xem panel `cost` (`sum(cost_usd) by 1m` và tổng) — xác định cost tăng đột biến hay tăng dần đều, và thời điểm bắt đầu lệch khỏi baseline.
  2. **Traces**: xem trace có `tokens_in`/`tokens_out` bất thường cao — request nào đang tốn token nhiều hơn dự kiến (input quá dài, hay agent loop gọi tool/LLM nhiều lần).
  3. **Logs**: đối chiếu `feature`/`model` trong log các request `response_sent` có `cost_usd` cao — xác định cost tăng tập trung ở feature/model nào.
- Mitigation tạm thời: nếu do một feature cụ thể gọi model đắt tiền quá mức cần thiết, tạm giới hạn concurrency hoặc chuyển feature đó sang model rẻ hơn; rollback bằng cách trả lại model/cấu hình gốc sau khi đã tối ưu (ví dụ giảm token input, cache câu trả lời lặp lại).
- Owner: C (Metrics & Dashboard) — chủ sở hữu đo đếm cost; phối hợp A nếu nguyên nhân nằm ở logic gọi model trong agent.
- Escalation/owner: nếu cost vượt >2x ngân sách (>5 USD) trong cùng khoảng đánh giá, escalate cho E để quyết định có tạm dừng feature liên quan không.
- Điều kiện đóng incident: cost trong khoảng đánh giá tiếp theo quay lại ≤2.5 USD và đã xác định + xử lý nguyên nhân tăng chi phí (không chỉ vì traffic giảm tạm thời).
- Cách xác minh recovery: theo dõi panel `cost` ở khoảng đánh giá kế tiếp, xác nhận tổng cost nằm dưới ngân sách với mức traffic tương đương giai đoạn trước breach.
