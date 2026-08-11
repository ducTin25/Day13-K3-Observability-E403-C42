# CP2 Evidence — Agent, RAG & LLM Tracing

## Kết luận

- Đã tạo 20 traces cho hai workload có cùng input và concurrency 5.
- Mỗi trace có metadata `correlation_id`, `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`.
- Waterfall có đúng quan hệ cha-con `agent.run → rag.retrieve` và `agent.run → llm.generate`.
- LLM generation có model, token usage và cost.
- Input/output của cả ba observations đều `null`; không capture raw PII.

## Danh sách 10 baseline traces

| Trace ID | Correlation ID | Prompt |
|---|---|---|
| `af36163c0d92e942321861e7fe1ed87a` | `req-6399c16a` | baseline v1 |
| `881c94fb5802bd336864733489735b46` | `req-768cee9d` | baseline v1 |
| `89b5610f2633df39ab210a9d6b90c40a` | `req-0fffc98c` | baseline v1 |
| `a09809ea38be5f2956b7f4cf2ff034e0` | `req-ce1edbf0` | baseline v1 |
| `562f0d19d0488138b9bff4ccd6f63b18` | `req-959c5b22` | baseline v1 |
| `72b00946e4196a0f3c413a4b4d47063a` | `req-d71a24df` | baseline v1 |
| `8a761e31b81cc3cdaff94536bee0c976` | `req-1440d58a` | baseline v1 |
| `bb19d78c2d1aa24c8731801f6b809615` | `req-55c5e6f8` | baseline v1 |
| `a9f7b7d55e022167ce732ede145f0097` | `req-c936e22e` | baseline v1 |
| `61d670c4c3b9afaeb93a6a29a9c54dd8` | `req-941df672` | baseline v1 |

## Danh sách 10 practice `rag_slow` traces

| Trace ID | Correlation ID | Agent latency |
|---|---|---:|
| `e495d0be43d3b423b169448f6db1a589` | `req-544857e1` | 2.653 s |
| `219e67ebbbc81281451ff978e76d0a9f` | `req-e1e31bd0` | 2.651 s |
| `513afbc8e0a20c589a54d5151ce93a77` | `req-470693f7` | 2.651 s |
| `d8c91ff82adbbbfcc4ad1ec3412405c7` | `req-5bd2692a` | 2.658 s |
| `f6818b5c3da43f2fb10e68527dd89c24` | `req-ba6576a6` | 2.652 s |
| `49e48b58d59f2a2ef699305be114413b` | `req-4df16668` | 2.652 s |
| `d167e5dd4cd79f7d686c366bcd4f8cac` | `req-0788af20` | 2.652 s |
| `4c857f138bb99b08901b723bae89c82e` | `req-5469225c` | 2.652 s |
| `4b6f874d92328898ffddca9b463ea30f` | `req-38d10a38` | 2.651 s |
| `140deeeeacae5bbc21e7a21f3b88c876` | `req-feb8e22a` | 2.652 s |

## Waterfall before/after

| Workload | Trace ID | Agent | RAG | LLM |
|---|---|---:|---:|---:|
| Baseline | `bb19d78c2d1aa24c8731801f6b809615` | 0.151 s | ~0.000 s | 0.151 s |
| Practice `rag_slow` | `140deeeeacae5bbc21e7a21f3b88c876` | 2.652 s | 2.501 s | 0.151 s |

Trong trace practice, RAG chiếm khoảng 94% tổng agent latency; LLM không tăng so với baseline. Đây là evidence practice, không phải kết luận cho official challenge CP3.

## LLM generation detail

Trace `140deeeeacae5bbc21e7a21f3b88c876`, observation `llm.generate`:

```text
model: claude-sonnet-4-5
prompt_tokens: 28
completion_tokens: 137
total_tokens: 165
total_cost_usd: 0.002139
input: null
output: null
```

## Trace → Log correlation

- Trace ID: `140deeeeacae5bbc21e7a21f3b88c876`.
- Correlation ID: `req-feb8e22a`.
- JSON log evidence: [`cp2-correlation-log.txt`](cp2-correlation-log.txt).
- Load-test outputs: [`cp2-load-baseline.txt`](cp2-load-baseline.txt) và [`cp2-load-rag-slow.txt`](cp2-load-rag-slow.txt).

## Evidence UI còn cần bổ sung

Trước khi nộp, nhóm vẫn nên chụp Langfuse waterfall và trace list vào `submission/evidence/` để đáp ứng yêu cầu ảnh trong hướng dẫn nộp bài.
