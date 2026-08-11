from __future__ import annotations

import json
from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.trace_updates: list[dict] = []
        self.span_starts: list[dict] = []
        self.span_updates: list[dict] = []
        self.generation_starts: list[dict] = []
        self.generation_updates: list[dict] = []
        self.events: list[str] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_trace(self, **kwargs) -> None:
        self.events.append("trace_update")
        self.trace_updates.append(kwargs)

    @contextmanager
    def start_as_current_span(self, **kwargs):
        self.events.append(f"span_start:{kwargs['name']}")
        self.span_starts.append(kwargs)
        yield self
        self.events.append(f"span_end:{kwargs['name']}")

    def update_current_span(self, **kwargs) -> None:
        self.events.append("span_update")
        self.span_updates.append(kwargs)

    @contextmanager
    def start_as_current_generation(self, **kwargs):
        self.events.append(f"generation_start:{kwargs['name']}")
        self.generation_starts.append(kwargs)
        yield self
        self.events.append(f"generation_end:{kwargs['name']}")

    def update_current_generation(self, **kwargs) -> None:
        self.events.append("generation_update")
        self.generation_updates.append(kwargs)


def test_agent_links_prompt_version_to_trace_and_generation(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces for private@example.test",
        correlation_id="req-e0000001",
    )

    trace_metadata = client.trace_updates[-1]["metadata"]
    generation_update = client.generation_updates[-1]
    assert trace_metadata == {
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "correlation_id": "req-e0000001",
    }
    assert client.span_starts == [
        {"name": "rag.retrieve", "metadata": {"component": "rag"}}
    ]
    assert client.span_updates == [
        {"metadata": {"component": "rag", "doc_count": 1}}
    ]
    assert client.generation_starts[-1]["name"] == "llm.generate"
    assert client.generation_starts[-1]["model"] == agent.model
    assert generation_update["prompt"] is client.prompt
    assert generation_update["metadata"]["prompt_version"] == "3"
    assert generation_update["metadata"]["correlation_id"] == "req-e0000001"
    assert generation_update["usage_details"]["prompt_tokens"] > 0
    assert generation_update["usage_details"]["completion_tokens"] > 0
    assert generation_update["cost_details"]["total"] > 0
    assert client.events == [
        "span_start:rag.retrieve",
        "span_update",
        "span_end:rag.retrieve",
        "trace_update",
        "generation_start:llm.generate",
        "generation_update",
        "generation_end:llm.generate",
    ]

    recorded = json.dumps(
        {
            "trace_updates": client.trace_updates,
            "span_starts": client.span_starts,
            "span_updates": client.span_updates,
            "generation_updates": client.generation_updates,
        },
        default=str,
    )
    assert "private@example.test" not in recorded
    assert "[REDACTED_EMAIL]" in recorded
