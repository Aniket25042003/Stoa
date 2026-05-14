"""LLM provider abstraction with manual switch + auto-failover.

Behavior summary (driven by env vars):

- ``GTM_LLM_PROVIDER`` selects the *primary* provider. ``vertex`` (default)
  uses Google Vertex AI (Gemini); ``openai`` uses OpenAI Chat Completions.
  This is the **manual** override the operator controls.
- ``GTM_LLM_AUTO_FAILOVER`` (default ``true``) controls whether we
  automatically fall through to the other provider **only when the primary
  is down** (raises an exception — auth, quota, network, 5xx, etc.).
  Quality-based switching is intentionally NOT automatic; flip
  ``GTM_LLM_PROVIDER`` to change the active model.
- If neither provider can be constructed (missing creds / packages), the
  caller receives ``None`` so the deterministic non-LLM fallback path
  continues to work, exactly as before.

This module is the *only* place that imports ``ChatVertexAI`` /
``ChatOpenAI``. Everything else calls :func:`invoke_json`.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

logger = logging.getLogger(__name__)

PROVIDER_VERTEX = "vertex"
PROVIDER_OPENAI = "openai"
_VALID_PROVIDERS = (PROVIDER_VERTEX, PROVIDER_OPENAI)
TaskTier = Literal["cheap", "standard", "premium"]


def _truthy(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class ProviderResult:
    """Outcome of a single provider attempt."""

    provider: str
    content: str | None
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.content is not None


@dataclass(frozen=True)
class LLMConfig:
    """Resolved provider configuration. Built once from env via :func:`load_config`."""

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
    temperature: float = 0.25
    timeout_seconds: float = 60.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def fallback(self) -> str:
        return PROVIDER_OPENAI if self.primary == PROVIDER_VERTEX else PROVIDER_VERTEX

    @property
    def chain(self) -> tuple[str, ...]:
        return (self.primary, self.fallback) if self.auto_failover else (self.primary,)

    def model_for(self, provider: str, task_tier: TaskTier) -> str | None:
        if provider == PROVIDER_VERTEX:
            if task_tier in ("cheap", "standard"):
                return self.vertex_model_fast or self.vertex_model
            return self.vertex_model_pro or self.vertex_model
        if provider == PROVIDER_OPENAI:
            if task_tier in ("cheap", "standard"):
                return self.openai_model_fast or self.openai_model
            return self.openai_model_pro or self.openai_model
        return None


def load_config() -> LLMConfig:
    """Read env vars into an :class:`LLMConfig`. Cheap; safe to call per-request."""
    raw_provider = (os.getenv("GTM_LLM_PROVIDER") or PROVIDER_VERTEX).strip().lower()
    if raw_provider not in _VALID_PROVIDERS:
        logger.warning("Unknown GTM_LLM_PROVIDER=%r; defaulting to %s", raw_provider, PROVIDER_VERTEX)
        raw_provider = PROVIDER_VERTEX

    openai_model = (
        os.getenv("GTM_OPENAI_MODEL")
        or os.getenv("GTM_AGENT_MODEL")
        or os.getenv("GTM_SYNTHESIS_MODEL")
    )
    openai_model_fast = os.getenv("GTM_OPENAI_MODEL_FAST") or openai_model
    openai_model_pro = os.getenv("GTM_OPENAI_MODEL_PRO") or openai_model
    vertex_model = os.getenv("GTM_VERTEX_MODEL") or "gemini-2.5-pro"

    try:
        temperature = float(os.getenv("GTM_LLM_TEMPERATURE") or 0.25)
    except ValueError:
        temperature = 0.25

    return LLMConfig(
        primary=raw_provider,
        auto_failover=_truthy(os.getenv("GTM_LLM_AUTO_FAILOVER"), default=True),
        vertex_model=vertex_model,
        vertex_model_fast=os.getenv("GTM_VERTEX_MODEL_FAST") or "gemini-2.5-flash",
        vertex_model_pro=os.getenv("GTM_VERTEX_MODEL_PRO") or vertex_model,
        vertex_project=os.getenv("GTM_VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT"),
        vertex_location=os.getenv("GTM_VERTEX_LOCATION") or "us-central1",
        openai_model=openai_model,
        openai_model_fast=openai_model_fast,
        openai_model_pro=openai_model_pro,
        temperature=temperature,
        timeout_seconds=_env_float("GTM_LLM_TIMEOUT_SECONDS", 60.0),
    )


def _vertex_invocation(cfg: LLMConfig, task_tier: TaskTier = "standard") -> Callable[[list[tuple[str, str]]], str] | None:
    """Build a Vertex callable, or return ``None`` if not configured/installed.

    Vertex auth resolves via ``google.auth`` (ADC) — i.e. one of:
    ``GOOGLE_APPLICATION_CREDENTIALS`` pointing at a service-account JSON,
    a ``gcloud auth application-default login`` session, or workload identity
    on GCP. We do not validate creds eagerly; ``ChatVertexAI`` raises on
    invoke if they are missing, which our failover loop treats as "down".
    """
    try:
        from langchain_google_vertexai import ChatVertexAI  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - import guarded for envs without the package
        logger.debug("Vertex provider unavailable: %s", exc)
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
        logger.warning("Failed to initialize ChatVertexAI: %s", exc)
        return None

    def _invoke(messages: list[tuple[str, str]]) -> str:
        msg = llm.invoke(messages)
        return str(getattr(msg, "content", "") or "")

    return _invoke


def _openai_invocation(cfg: LLMConfig, task_tier: TaskTier = "standard") -> Callable[[list[tuple[str, str]]], str] | None:
    """Build an OpenAI callable, or return ``None`` if not configured."""
    model = cfg.model_for(PROVIDER_OPENAI, task_tier)
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        logger.debug("OpenAI provider unavailable: %s", exc)
        return None

    try:
        llm = ChatOpenAI(model=model, temperature=cfg.temperature, timeout=cfg.timeout_seconds)
    except Exception as exc:
        logger.warning("Failed to initialize ChatOpenAI: %s", exc)
        return None

    def _invoke(messages: list[tuple[str, str]]) -> str:
        msg = llm.invoke(messages)
        return str(getattr(msg, "content", "") or "")

    return _invoke


_BUILDERS: dict[str, Callable[..., Callable[[list[tuple[str, str]]], str] | None]] = {
    PROVIDER_VERTEX: _vertex_invocation,
    PROVIDER_OPENAI: _openai_invocation,
}


def _strip_code_fence(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    return text


def invoke_json(
    system: str,
    payload: dict[str, Any],
    max_chars: int = 16000,
    *,
    config: LLMConfig | None = None,
    task_tier: TaskTier = "standard",
) -> tuple[dict[str, Any] | None, str | None]:
    """Run the prompt through the provider chain; return ``(parsed_json, provider_used)``.

    ``provider_used`` is the provider name that produced the result, or
    ``None`` if every provider was either unavailable or errored. We return
    a tuple (rather than raising) so callers can fall through to their
    deterministic non-LLM behavior, matching the previous contract of
    ``_llm_json``.
    """
    cfg = config or load_config()
    messages: list[tuple[str, str]] = [
        ("system", system + "\nReturn only valid JSON. Do not wrap it in markdown."),
        ("human", json.dumps(payload, default=str)[:max_chars]),
    ]

    last_error: BaseException | None = None
    for provider_name in cfg.chain:
        try:
            invoker = _BUILDERS[provider_name](cfg, task_tier=task_tier)
        except TypeError:
            # Backward-compatible for tests or local monkeypatches that still
            # provide the old one-argument builder signature.
            invoker = _BUILDERS[provider_name](cfg)
        if invoker is None:
            logger.debug("Provider %s not available; trying next", provider_name)
            continue
        try:
            content = invoker(messages)
        except Exception as exc:
            # "Down" path: log + try the next provider in the chain.
            last_error = exc
            logger.warning("LLM provider %s failed: %s", provider_name, exc)
            continue
        try:
            parsed = json.loads(_strip_code_fence(content))
        except (json.JSONDecodeError, TypeError) as exc:
            last_error = exc
            logger.warning("Provider %s returned non-JSON content; trying next provider", provider_name)
            continue
        if isinstance(parsed, dict):
            return parsed, provider_name
        # Non-dict JSON (list/scalar) is treated like a soft failure for our usage.
        logger.debug("Provider %s returned non-object JSON; ignoring", provider_name)

    if last_error is not None:
        logger.info("All LLM providers exhausted; falling back to deterministic path")
    return None, None


__all__ = [
    "LLMConfig",
    "PROVIDER_OPENAI",
    "PROVIDER_VERTEX",
    "ProviderResult",
    "invoke_json",
    "load_config",
]
