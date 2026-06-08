"""LLM provider abstraction with task-tier routing and auto-failover."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from stoa_core.config import get_settings

logger = logging.getLogger(__name__)

MessageFn = Callable[[list[tuple[str, str]]], str]

PROVIDER_VERTEX = "vertex"
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
_VALID_PROVIDERS = (PROVIDER_VERTEX, PROVIDER_OPENAI, PROVIDER_ANTHROPIC)
TaskTier = Literal["cheap", "standard", "premium"]

TASK_TIER_MAP: dict[str, TaskTier] = {
    "classify": "cheap",
    "extract": "cheap",
    "tag": "cheap",
    "summarize": "standard",
    "synthesize": "premium",
    "icp_build": "premium",
    "campaign_plan": "premium",
}


def _truthy(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class LLMConfig:
    primary: str = PROVIDER_VERTEX
    auto_failover: bool = True
    vertex_model: str = "gemini-2.5-pro"
    vertex_model_fast: str = "gemini-2.5-flash"
    vertex_model_pro: str = "gemini-2.5-pro"
    vertex_project: str | None = None
    vertex_location: str = "us-central1"
    openai_model: str | None = None
    openai_model_fast: str | None = None
    openai_model_pro: str | None = None
    anthropic_model: str | None = None
    anthropic_model_fast: str | None = None
    anthropic_model_pro: str | None = None
    temperature: float = 0.25
    timeout_seconds: float = 60.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def fallback_chain(self) -> tuple[str, ...]:
        if self.primary == PROVIDER_VERTEX:
            chain = [PROVIDER_OPENAI, PROVIDER_ANTHROPIC]
        elif self.primary == PROVIDER_OPENAI:
            chain = [PROVIDER_VERTEX, PROVIDER_ANTHROPIC]
        else:
            chain = [PROVIDER_VERTEX, PROVIDER_OPENAI]
        if self.auto_failover:
            return (self.primary, *chain)
        return (self.primary,)

    def model_for(self, provider: str, task_tier: TaskTier) -> str | None:
        fast = task_tier in ("cheap", "standard")
        if provider == PROVIDER_VERTEX:
            return (self.vertex_model_fast if fast else self.vertex_model_pro) or self.vertex_model
        if provider == PROVIDER_OPENAI:
            return (self.openai_model_fast if fast else self.openai_model_pro) or self.openai_model
        if provider == PROVIDER_ANTHROPIC:
            fast_model = self.anthropic_model_fast if fast else self.anthropic_model_pro
            return fast_model or self.anthropic_model
        return None


BuilderFn = Callable[[LLMConfig, TaskTier], MessageFn | None]


def load_config() -> LLMConfig:
    s = get_settings()
    raw = (os.getenv("STOA_LLM_PROVIDER") or s.llm_provider or PROVIDER_VERTEX).strip().lower()
    if raw not in _VALID_PROVIDERS:
        raw = PROVIDER_VERTEX
    return LLMConfig(
        primary=raw,
        auto_failover=_truthy(os.getenv("STOA_LLM_AUTO_FAILOVER"), default=s.llm_auto_failover),
        vertex_model=s.resolved_vertex_model,
        vertex_model_fast=s.resolved_vertex_model_fast,
        vertex_model_pro=s.vertex_model_pro,
        vertex_project=s.resolved_vertex_project or os.getenv("GOOGLE_CLOUD_PROJECT"),
        vertex_location=s.resolved_vertex_location,
        openai_model=s.openai_model or os.getenv("OPENAI_MODEL"),
        openai_model_fast=s.openai_model_fast,
        openai_model_pro=s.openai_model_pro,
        anthropic_model=s.anthropic_model or os.getenv("ANTHROPIC_MODEL"),
        anthropic_model_fast=os.getenv("ANTHROPIC_MODEL_FAST"),
        anthropic_model_pro=os.getenv("ANTHROPIC_MODEL_PRO"),
        temperature=s.llm_temperature,
        timeout_seconds=s.llm_timeout_seconds,
    )


def _vertex_invocation(cfg: LLMConfig, task_tier: TaskTier) -> MessageFn | None:
    try:
        from langchain_google_vertexai import ChatVertexAI
    except Exception as exc:
        logger.debug("Vertex unavailable: %s", exc)
        return None
    kwargs: dict[str, Any] = {
        "model": cfg.model_for(PROVIDER_VERTEX, task_tier) or cfg.vertex_model,
        "temperature": cfg.temperature,
        "request_timeout": cfg.timeout_seconds,
    }
    if cfg.vertex_project:
        kwargs["project"] = cfg.vertex_project
    if cfg.vertex_location:
        kwargs["location"] = cfg.vertex_location
    try:
        llm = ChatVertexAI(**kwargs)
    except Exception as exc:
        logger.warning("ChatVertexAI init failed: %s", exc)
        return None

    def _invoke(messages: list[tuple[str, str]]) -> str:
        return str(getattr(llm.invoke(messages), "content", "") or "")

    return _invoke


def _openai_invocation(cfg: LLMConfig, task_tier: TaskTier) -> MessageFn | None:
    model = cfg.model_for(PROVIDER_OPENAI, task_tier)
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI
    except Exception as exc:
        logger.debug("OpenAI unavailable: %s", exc)
        return None
    try:
        llm = ChatOpenAI(model=model, temperature=cfg.temperature, timeout=cfg.timeout_seconds)
    except Exception as exc:
        logger.warning("ChatOpenAI init failed: %s", exc)
        return None

    def _invoke(messages: list[tuple[str, str]]) -> str:
        return str(getattr(llm.invoke(messages), "content", "") or "")

    return _invoke


def _anthropic_invocation(cfg: LLMConfig, task_tier: TaskTier) -> MessageFn | None:
    model = cfg.model_for(PROVIDER_ANTHROPIC, task_tier)
    if not model or not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        from langchain_anthropic import ChatAnthropic
    except Exception as exc:
        logger.debug("Anthropic unavailable: %s", exc)
        return None
    try:
        llm = ChatAnthropic(model=model, temperature=cfg.temperature, timeout=cfg.timeout_seconds)
    except Exception as exc:
        logger.warning("ChatAnthropic init failed: %s", exc)
        return None

    def _invoke(messages: list[tuple[str, str]]) -> str:
        return str(getattr(llm.invoke(messages), "content", "") or "")

    return _invoke


_BUILDERS: dict[str, BuilderFn] = {
    PROVIDER_VERTEX: _vertex_invocation,
    PROVIDER_OPENAI: _openai_invocation,
    PROVIDER_ANTHROPIC: _anthropic_invocation,
}


def _strip_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return text


def _invoke_chain(
    messages: list[tuple[str, str]],
    *,
    config: LLMConfig | None = None,
    task_tier: TaskTier = "standard",
) -> tuple[str | None, str | None]:
    cfg = config or load_config()
    for provider in cfg.fallback_chain:
        invoker = _BUILDERS.get(provider)
        if not invoker:
            continue
        fn = invoker(cfg, task_tier)
        if fn is None:
            continue
        try:
            return fn(messages), provider
        except Exception as exc:
            logger.warning("LLM provider %s failed: %s", provider, exc)
    return None, None


def invoke_text(
    system: str,
    user: str,
    *,
    config: LLMConfig | None = None,
    task_tier: TaskTier = "standard",
    task_name: str | None = None,
) -> tuple[str | None, str | None]:
    tier = TASK_TIER_MAP.get(task_name or "", task_tier)
    messages = [("system", system), ("human", user)]
    return _invoke_chain(messages, config=config, task_tier=tier)


def invoke_json(
    system: str,
    payload: dict[str, Any],
    max_chars: int = 16000,
    *,
    config: LLMConfig | None = None,
    task_tier: TaskTier = "standard",
    task_name: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    tier = TASK_TIER_MAP.get(task_name or "", task_tier)
    messages = [
        ("system", system + "\nReturn only valid JSON. Do not wrap in markdown."),
        ("human", json.dumps(payload, default=str)[:max_chars]),
    ]
    content, provider = _invoke_chain(messages, config=config, task_tier=tier)
    if content is None:
        return None, None
    try:
        parsed = json.loads(_strip_fence(content))
        if isinstance(parsed, dict):
            return parsed, provider
    except json.JSONDecodeError:
        logger.warning("Non-JSON response from %s", provider)
    return None, provider
