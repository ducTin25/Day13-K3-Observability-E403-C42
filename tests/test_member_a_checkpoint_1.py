from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app import main as main_module
from app.pii import hash_user_id


def _read_events(log_path: Path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def _chat_payload() -> dict[str, str]:
    return {
        "user_id": "student-01",
        "session_id": "session-01",
        "feature": "qa",
        "message": "Explain observability",
    }


def test_chat_propagates_valid_correlation_id_and_context(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    correlation_id = "req-deadbeef"

    with TestClient(main_module.app) as client:
        response = client.post("/chat", json=_chat_payload(), headers={"x-request-id": correlation_id})

    assert response.status_code == 200
    assert response.json()["correlation_id"] == correlation_id
    assert response.headers["x-request-id"] == correlation_id
    assert float(response.headers["x-response-time-ms"]) >= 0

    api_events = [event for event in _read_events(log_path) if event.get("service") == "api"]
    assert {event["event"] for event in api_events} == {"request_received", "response_sent"}
    for event in api_events:
        assert event["correlation_id"] == correlation_id
        assert event["user_id_hash"] == hash_user_id("student-01")
        assert event["session_id"] == "session-01"
        assert event["feature"] == "qa"
        assert event["model"] == main_module.agent.model
        assert event["env"] == "dev"
        assert "student-01" not in json.dumps(event)


def test_invalid_correlation_id_is_replaced(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(main_module.app) as client:
        response = client.post("/chat", json=_chat_payload(), headers={"x-request-id": "not-safe"})

    correlation_id = response.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
    assert response.json()["correlation_id"] == correlation_id


def test_unhandled_error_is_safe_and_counted_once(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    recorded_errors: list[str] = []

    def fail_agent(**_: object) -> None:
        raise RuntimeError("Contact student@example.com for internal details")

    monkeypatch.setattr(main_module.agent, "run", fail_agent)
    monkeypatch.setattr(main_module, "record_error", recorded_errors.append)

    with TestClient(main_module.app, raise_server_exceptions=False) as client:
        response = client.post("/chat", json=_chat_payload())

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])
    assert response.json()["correlation_id"] == response.headers["x-request-id"]
    assert recorded_errors == ["RuntimeError"]

    failed_event = next(event for event in _read_events(log_path) if event["event"] == "request_failed")
    assert failed_event["error_type"] == "RuntimeError"
    assert failed_event["correlation_id"] == response.headers["x-request-id"]
    assert "student@example.com" not in json.dumps(failed_event)
