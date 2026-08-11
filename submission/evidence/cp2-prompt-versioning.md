# CP2 Evidence — Prompt Versioning

## Ownership

- Owner: Thành viên E — QA & Chief Investigator.
- Prompt name: `day13-chat`.
- Langfuse region: US (`https://us.cloud.langfuse.com`).
- Không có API key hoặc secret trong evidence này.

## Prompt versions

| Version | Nội dung chính | Labels cuối cùng |
|---:|---|---|
| 1 | `Feature={{feature}}`, `Docs={{docs}}`, `Question={{message}}` | `baseline`, `production` |
| 2 | Giữ ba biến bắt buộc, bổ sung hướng dẫn trả lời ngắn gọn | `candidate`, `latest` |

## Trace theo label

| Trường hợp | Correlation ID | Trace ID | Label | Version |
|---|---|---|---|---:|
| Baseline | `req-55c5e6f8` | `bb19d78c2d1aa24c8731801f6b809615` | `baseline` | 1 |
| Candidate | `req-e2222222` | `6d4e75fcb32c66ca2d4bf984d1cc9e30` | `candidate` | 2 |
| Production sau promote | `req-e2222223` | `1984d5d04a8c6e13d0bb44ea6bd208e2` | `production` | 2 |
| Production sau rollback | `req-e1111112` | `28b8becb0b8d543b3fa2663011b90a70` | `production` | 1 |

## Promote và rollback đã xác minh

Promote production sang v2:

```json
{"version": 2, "labels": ["candidate", "production", "latest"]}
```

Rollback production về v1:

```json
{"version": 1, "labels": ["baseline", "production"]}
```

Sau rollback, v2 còn labels `candidate`, `latest`; fetch theo `production` trả version 1. Hai request production trước/sau rollback tạo trace thật với version tương ứng, không sửa code để giả metadata.

## Evidence UI còn cần bổ sung

Theo hướng dẫn nộp bài, nhóm vẫn nên chụp giao diện Langfuse hiển thị danh sách hai versions và labels vào `submission/evidence/` trước khi nộp.
