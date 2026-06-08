"""Tests for the Vertex/OpenAI provider abstraction in ``gtm_agents.llm``.

These are pure unit tests: they monkeypatch the two provider builders so we
never touch the real Vertex / OpenAI APIs. They cover the four behaviors the
operator cares about:

1. Vertex is selected as primary by default.
2. ``GTM_LLM_PROVIDER=openai`` flips the primary (manual quality override).
3. When the primary raises (model "down") we auto-failover to the other.
4. ``GTM_LLM_AUTO_FAILOVER=false`` disables that and surfaces the failure
   as ``None`` (the deterministic non-LLM fallback the rest of the app uses).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import pytest

from gtm_agents import llm as llm_mod


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wipe every env var the LLM module reads so each test starts clean."""
    for key in (
        "GTM_LLM_PROVIDER",
        "GTM_LLM_AUTO_FAILOVER",
        "GTM_LLM_TEMPERATURE",
        "GTM_VERTEX_MODEL",
        "GTM_VERTEX_PROJECT",
        "GTM_VERTEX_LOCATION",
        "GTM_OPENAI_MODEL",
        "GTM_AGENT_MODEL",
        "GTM_SYNTHESIS_MODEL",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


def _stub_provider(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    *,
    response: dict[str, Any] | None = None,
    raises: BaseException | None = None,
    available: bool = True,
) -> dict[str, int]:
    """Replace ``_vertex_invocation`` / ``_openai_invocation`` with a stub.

    Returns a counter dict so tests can assert how many times each provider
    was actually invoked, which is how we verify failover order.
    """
    counter = {"calls": 0}

    def _builder(_cfg: llm_mod.LLMConfig) -> Callable[[list[tuple[str, str]]], str] | None:
        if not available:
            return None

        def _invoke(_messages: list[tuple[str, str]]) -> str:
            counter["calls"] += 1
            if raises is not None:
                raise raises
            return json.dumps(response or {})

        return _invoke

    target = "_vertex_invocation" if name == llm_mod.PROVIDER_VERTEX else "_openai_invocation"
    monkeypatch.setattr(llm_mod, target, _builder)
    monkeypatch.setitem(llm_mod._BUILDERS, name, _builder)
    return counter


def test_vertex_is_default_primary() -> None:
    cfg = llm_mod.load_config()
    assert cfg.primary == llm_mod.PROVIDER_VERTEX
    assert cfg.fallback == llm_mod.PROVIDER_OPENAI
    assert cfg.auto_failover is True
    assert cfg.chain == (llm_mod.PROVIDER_VERTEX, llm_mod.PROVIDER_OPENAI)


def test_manual_switch_to_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """The user-facing manual override: change provider via the env file."""
    monkeypatch.setenv("GTM_LLM_PROVIDER", "openai")
    cfg = llm_mod.load_config()
    assert cfg.primary == llm_mod.PROVIDER_OPENAI
    assert cfg.fallback == llm_mod.PROVIDER_VERTEX
    assert cfg.chain == (llm_mod.PROVIDER_OPENAI, llm_mod.PROVIDER_VERTEX)


def test_unknown_provider_falls_back_to_vertex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GTM_LLM_PROVIDER", "anthropic")  # not supported
    cfg = llm_mod.load_config()
    assert cfg.primary == llm_mod.PROVIDER_VERTEX


def test_disabling_auto_failover_yields_single_provider_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GTM_LLM_AUTO_FAILOVER", "false")
    cfg = llm_mod.load_config()
    assert cfg.chain == (llm_mod.PROVIDER_VERTEX,)


def test_invoke_uses_primary_when_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    vertex_calls = _stub_provider(monkeypatch, llm_mod.PROVIDER_VERTEX, response={"hello": "from-vertex"})
    openai_calls = _stub_provider(monkeypatch, llm_mod.PROVIDER_OPENAI, response={"hello": "from-openai"})

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})

    assert used == llm_mod.PROVIDER_VERTEX
    assert parsed == {"hello": "from-vertex"}
    assert vertex_calls["calls"] == 1
    assert openai_calls["calls"] == 0  # fallback not used when primary works


def test_auto_failover_when_primary_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vertex throws (simulating quota / 5xx / auth) → we use OpenAI."""
    vertex_calls = _stub_provider(
        monkeypatch,
        llm_mod.PROVIDER_VERTEX,
        raises=RuntimeError("503 service unavailable"),
    )
    openai_calls = _stub_provider(monkeypatch, llm_mod.PROVIDER_OPENAI, response={"recovered": True})
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GTM_OPENAI_MODEL", "gpt-4o-mini")

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})

    assert vertex_calls["calls"] == 1
    assert openai_calls["calls"] == 1
    assert used == llm_mod.PROVIDER_OPENAI
    assert parsed == {"recovered": True}


def test_no_failover_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Operator opted out of failover; primary failure must surface as None."""
    monkeypatch.setenv("GTM_LLM_AUTO_FAILOVER", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GTM_OPENAI_MODEL", "gpt-4o-mini")
    vertex_calls = _stub_provider(
        monkeypatch,
        llm_mod.PROVIDER_VERTEX,
        raises=RuntimeError("vertex is down"),
    )
    openai_calls = _stub_provider(monkeypatch, llm_mod.PROVIDER_OPENAI, response={"should": "not-be-used"})

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})

    assert vertex_calls["calls"] == 1
    assert openai_calls["calls"] == 0
    assert parsed is None
    assert used is None


def test_returns_none_when_no_provider_available(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_provider(monkeypatch, llm_mod.PROVIDER_VERTEX, available=False)
    _stub_provider(monkeypatch, llm_mod.PROVIDER_OPENAI, available=False)

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})

    assert parsed is None
    assert used is None


def test_handles_markdown_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Models sometimes wrap output in ```json fences; we strip and parse."""

    def _builder(_cfg: llm_mod.LLMConfig) -> Callable[[list[tuple[str, str]]], str] | None:
        def _invoke(_messages: list[tuple[str, str]]) -> str:
            return '```json\n{"ok": true}\n```'

        return _invoke

    monkeypatch.setitem(llm_mod._BUILDERS, llm_mod.PROVIDER_VERTEX, _builder)

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})
    assert used == llm_mod.PROVIDER_VERTEX
    assert parsed == {"ok": True}


def test_non_json_response_attempts_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """If primary returns garbage, we try the fallback before giving up."""

    def _vertex_builder(_cfg: llm_mod.LLMConfig) -> Callable[[list[tuple[str, str]]], str] | None:
        def _invoke(_messages: list[tuple[str, str]]) -> str:
            return "I am sorry, I cannot answer that."

        return _invoke

    monkeypatch.setitem(llm_mod._BUILDERS, llm_mod.PROVIDER_VERTEX, _vertex_builder)
    openai_calls = _stub_provider(monkeypatch, llm_mod.PROVIDER_OPENAI, response={"clean": "json"})
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GTM_OPENAI_MODEL", "gpt-4o-mini")

    parsed, used = llm_mod.invoke_json("system", {"k": "v"})

    assert used == llm_mod.PROVIDER_OPENAI
    assert parsed == {"clean": "json"}
    assert openai_calls["calls"] == 1


def test_legacy_openai_env_aliases_are_honored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing deployments rely on GTM_AGENT_MODEL — keep it working."""
    monkeypatch.setenv("GTM_AGENT_MODEL", "legacy-gpt-4o")
    cfg = llm_mod.load_config()
    assert cfg.openai_model == "legacy-gpt-4o"
