# Thành viên D — SRE & Alerts Engineer

## Phạm vi phụ trách

Thành viên D chịu trách nhiệm SLI/SLO, alert rules, severity/ownership và runbook xử lý sự cố. D bảo đảm alert dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Trạng thái repo hiện tại

- `config/slo.yaml` có bốn SLI mẫu nhưng latency còn ghi chú cần thay bằng target của nhóm.
- `config/alert_rules.yaml` còn toàn bộ placeholder `TODO` cho ba alert.
- `docs/alerts.md` mới là template, chưa có runbook thực tế.
- Dashboard có threshold latency 3000 ms, error 2%, cost 2.5 USD và quality 0.75.
- Chưa có test/validator chuyên sâu cho semantic của alert rules và runbook.

## Checkpoint 0 — Baseline và SLO assumptions

### Task

- Đọc workload, dashboard contract và baseline metrics.
- Xác định service boundary: API chat và trải nghiệm người dùng cần bảo vệ.
- Liệt kê SLI, đơn vị, nguồn dữ liệu và owner.
- Ghi rõ giả định vì lab ngắn nhưng SLO window mẫu là 28 ngày.

### Acceptance criteria

- Mỗi SLI có source field/event rõ ràng.
- Target không được chọn chỉ để baseline hiện tại luôn pass.
- Có lý do gắn với tác động người dùng hoặc ngân sách vận hành.

### Blocker/dependency

- Cần baseline và công thức metric từ C.
- Log/metrics chưa hoàn chỉnh cho đến khi A/C hoàn thành CP1.

## Checkpoint 1 — Chốt SLI/SLO contract

### Task

- Rà soát bốn SLI hiện có:
  - latency P95 ≤ 3000 ms;
  - error rate ≤ 2%;
  - daily cost ≤ 2.5 USD;
  - quality average ≥ 0.75.
- Xác nhận target compliance và window 28d có ý nghĩa gì trong lab/demo.
- Đồng bộ `error_rate_pct` với định nghĩa của C.
- Ghi rõ dữ liệu thiếu/không có traffic thì đánh giá SLO thế nào.
- Xác định warning threshold và critical threshold nếu cần hai mức.

### Acceptance criteria

- `config/slo.yaml` không còn ghi chú placeholder cần nhóm thay thế.
- SLO, dashboard threshold và alert condition không mâu thuẫn.
- Có thể giải thích vì sao chọn percentile thay vì average latency.

### Blocker/dependency

- Phụ thuộc C chốt mẫu số error rate.
- Cần A bảo đảm mỗi error chỉ được đếm một lần.

## Checkpoint 2 — Alert rules và runbook

### Task D1 — Hoàn thiện ba alert rules

Tạo ít nhất ba symptom-based alert, ví dụ:

- High latency/P95 breach.
- High error rate.
- Quality degradation hoặc cost budget risk.

Mỗi rule cần:

- Tên rõ ràng, không còn `TODO`.
- Severity hợp lý.
- Condition có threshold và khoảng thời gian duy trì.
- Type `symptom-based`.
- Owner cụ thể.
- Link đúng anchor runbook.

### Task D2 — Hoàn thiện runbook

Mỗi alert trong `docs/alerts.md` cần:

- SLI/SLO liên quan.
- Điều kiện kích hoạt và thời gian duy trì.
- Ảnh hưởng tới người dùng.
- Ba bước kiểm tra đầu tiên theo Metrics → Traces → Logs.
- Mitigation tạm thời an toàn và có cách rollback.
- Escalation/owner và điều kiện đóng incident.
- Cách xác minh recovery sau mitigation.

### Task D3 — Dry run

- Dùng practice incident để xác minh latency alert có thể phát hiện triệu chứng.
- Kiểm tra alert không flapping với một sample đơn lẻ.
- Walk-through runbook cùng C và E.
- Ghi nhận thời điểm detect, acknowledge, investigate và recover nếu mô phỏng được.

### Acceptance criteria

- Không còn placeholder trong `config/alert_rules.yaml` và `docs/alerts.md`.
- Alert condition dùng đúng metric/đơn vị của dashboard.
- Mỗi alert có runbook có thể thực thi mà không cần đoán bước tiếp theo.
- Alert không hard-code tên `rag_slow`, `tool_fail` hoặc `cost_spike` làm điều kiện triệu chứng.

### Blocker/dependency

- Phụ thuộc C cung cấp metric/dashboard runtime.
- Phụ thuộc A/B cung cấp log tin cậy và an toàn.
- Repo không cung cấp alert engine thực; cần ghi rõ alert rules là spec nếu nhóm không triển khai runtime evaluator.

## Checkpoint 3 — Challenge và incident response

### Task

- Dùng alert/runbook để định hướng điều tra, không đọc trước implementation để kết luận.
- Ghi severity, impacted SLO, time window và user impact.
- Đề xuất mitigation tạm thời cho symptom quan sát được.
- Sau fix/disable incident, xác minh metric quay về dưới threshold.
- Bàn giao preventive measures cho E đưa vào report.

### Blocker/dependency

- Challenge đã release.
- Evidence metric phụ thuộc C; trace/log evidence phụ thuộc E/A.

## Hoàn tất và bàn giao

- Commit/PR cho `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md` và tests/validator bổ sung nếu có.
- Bảng mapping SLI → SLO → dashboard panel → alert → runbook.
- Evidence dry run alert/runbook.
- Danh sách mitigation và điều kiện recovery.
- Ghi phần đóng góp cá nhân và commit SHA vào `submission/REPORT.md`.

## Thứ tự thực hiện đề xuất

1. Nhận baseline/metric contract từ C.
2. Chốt SLO và thresholds.
3. Viết ba alert rules.
4. Viết runbook tương ứng.
5. Dry run practice incident.
6. Hỗ trợ E trong challenge và preventive measures.
