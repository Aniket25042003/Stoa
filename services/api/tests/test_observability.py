"""Tests for LangSmith observability helpers (no network)."""

from gtm_agents.observability import redact_value, summarize_run_input, tracing_enabled_from_env


def test_redact_value_masks_secrets() -> None:
    payload = {
        "user": "alice",
        "api_key": "secret123",
        "nested": {"Authorization": "Bearer x", "ok": 1},
    }
    out = redact_value(payload)
    assert isinstance(out, dict)
    assert out["api_key"] == "<redacted>"
    assert out["nested"]["Authorization"] == "<redacted>"
    assert out["user"] == "alice"


def test_summarize_run_input_bounds_description() -> None:
    long_desc = "x" * 2000
    s = summarize_run_input({"product_description": long_desc, "product_name": "P"})
    assert isinstance(s, dict)
    assert "product_name" in s
    assert len(str(s.get("product_description", ""))) <= 900


def test_tracing_enabled_respects_langsmith_env(monkeypatch) -> None:
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    assert tracing_enabled_from_env() is False
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert tracing_enabled_from_env() is True
