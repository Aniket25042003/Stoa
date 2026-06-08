from stoa_core.security.pii import redact_json, redact_pii, redact_pii_for_logs


def test_redact_email():
    assert "[EMAIL]" in redact_pii("Contact user@example.com today")


def test_redact_phone_international():
    assert "[PHONE]" in redact_pii("Call +44 20 7946 0958")


def test_redact_iban():
    assert "[IBAN]" in redact_pii("Account GB82WEST12345698765432")


def test_redact_ssn():
    assert "[SSN]" in redact_pii("SSN 123-45-6789")


def test_redact_api_key():
    assert "[API_KEY]" in redact_pii("key sk-abcdefghijklmnopqrstuvwxyz123456")


def test_redact_jwt():
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    assert "[JWT]" in redact_pii(f"token {token}")


def test_redact_logs_include_ip():
    assert "[IP]" in redact_pii_for_logs("client 203.0.113.10 connected")
    assert "203.0.113.10" in redact_pii("client 203.0.113.10 connected")


def test_redact_json_nested():
    out = redact_json({"email": "a@b.com", "items": ["+15550109999"]})
    assert out["email"] == "[EMAIL]"
    assert out["items"][0] == "[PHONE]"
