from app.logging_config import scrub_event
from app.pii import hash_user_id, scrub_text, summarize_text


# Synthetic Test Dataset for Member B (Security Engineer)
SYNTHETIC_PII_DATASET = {
    "email": ["student@vinuni.edu.vn", "user.test+label@domain.co"],
    "phone_vn": ["0901234567", "090 123 4567", "090.123.4567", "090-123-4567", "+84 90 123 4567"],
    "cccd": ["001099123456", "079123456789"],
    "credit_card": ["4111 2222 3333 4444", "4111-2222-3333-4444"],
    "passport": ["B1234567", "C9876543"],
    "address_vn": ["Phường Bến Thành, Quận 1, TP. Hồ Chí Minh", "123 Đường Nguyễn Trãi, Phường 2, Quận 5"],
}


def test_scrub_email() -> None:
    for email in SYNTHETIC_PII_DATASET["email"]:
        out = scrub_text(f"Contact email: {email}")
        assert email not in out
        assert "[REDACTED_EMAIL]" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    for phone in SYNTHETIC_PII_DATASET["phone_vn"]:
        out = scrub_text(f"Contact phone: {phone}")
        assert phone not in out
        assert "[REDACTED_PHONE_VN]" in out


def test_scrub_cccd() -> None:
    for cccd in SYNTHETIC_PII_DATASET["cccd"]:
        out = scrub_text(f"ID card number: {cccd}")
        assert cccd not in out
        assert "[REDACTED_CCCD]" in out


def test_scrub_credit_card() -> None:
    for card in SYNTHETIC_PII_DATASET["credit_card"]:
        out = scrub_text(f"Payment card: {card}")
        assert card not in out
        assert "[REDACTED_CREDIT_CARD]" in out


def test_scrub_passport() -> None:
    for passport in SYNTHETIC_PII_DATASET["passport"]:
        out = scrub_text(f"Passport number: {passport}")
        assert passport not in out
        assert "[REDACTED_PASSPORT]" in out


def test_scrub_address_vn() -> None:
    for address in SYNTHETIC_PII_DATASET["address_vn"]:
        out = scrub_text(f"Address: {address}")
        assert address not in out
        assert "[REDACTED_ADDRESS_VN]" in out


def test_scrub_multiple_pii_in_single_string() -> None:
    text = "User test@domain.com with phone 0901234567 and passport B1234567"
    out = scrub_text(text)
    assert "test@domain.com" not in out
    assert "0901234567" not in out
    assert "B1234567" not in out
    assert "[REDACTED_EMAIL]" in out
    assert "[REDACTED_PHONE_VN]" in out
    assert "[REDACTED_PASSPORT]" in out


def test_hash_user_id() -> None:
    raw_id = "user_secret_123@domain.com"
    hashed = hash_user_id(raw_id)
    assert raw_id not in hashed
    assert len(hashed) == 12


def test_scrub_event_recursive_nested_payload() -> None:
    event_dict = {
        "event": "request_received",
        "service": "api",
        "correlation_id": "req-1234abcd",
        "latency_ms": 1448,
        "payload": {
            "user": {"email": "user@test.com", "phone": "0901234567"},
            "messages": ["My passport is B1234567", "Normal question"],
        },
    }
    result = scrub_event(None, "info", event_dict)
    assert result["correlation_id"] == "req-1234abcd"
    assert result["latency_ms"] == 1448
    assert "user@test.com" not in str(result["payload"])
    assert "0901234567" not in str(result["payload"])
    assert "B1234567" not in str(result["payload"])
    assert "[REDACTED_EMAIL]" in result["payload"]["user"]["email"]
    assert "[REDACTED_PHONE_VN]" in result["payload"]["user"]["phone"]
    assert "[REDACTED_PASSPORT]" in result["payload"]["messages"][0]


def test_negative_false_positives() -> None:
    # Technical IDs, metrics, and standard words must not be falsely redacted
    safe_text = "Event request_received with latency 1448ms, tokens 157, req-a1b2c3d4"
    out = scrub_text(safe_text)
    assert out == safe_text


