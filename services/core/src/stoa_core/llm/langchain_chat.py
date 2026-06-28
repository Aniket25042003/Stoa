"""Unified LangChain chat model factory (Google GenAI + fallbacks)."""

from __future__ import annotations

import logging
import os
from typing import Any

from stoa_core.config import get_settings
from stoa_core.llm.router import TaskTier, load_config

logger = logging.getLogger(__name__)

_warned_legacy_vertex = False


def build_chat_model(task_tier: TaskTier = "premium") -> Any | None:
    """Return a LangChain chat model for agent/tool-calling use."""
    global _warned_legacy_vertex
    cfg = load_config()
    settings = get_settings()

    if settings.llm_vertex_backend != "vertexai_legacy":
        genai_model = _build_google_genai(cfg, task_tier, settings)
        if genai_model is not None:
            return genai_model

    legacy = _build_legacy_vertex(cfg, task_tier)
    if legacy is not None:
        if not _warned_legacy_vertex:
            logger.warning(
                "Using deprecated ChatVertexAI; set llm_vertex_backend=genai for langchain-google-genai"
            )
            _warned_legacy_vertex = True
        return legacy

    openai_model = _build_openai(cfg, task_tier)
    if openai_model is not None:
        return openai_model

    return None


def _build_google_genai(cfg: Any, task_tier: TaskTier, settings: Any) -> Any | None:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:
        logger.debug("langchain-google-genai unavailable: %s", exc)
        return None

    model = cfg.model_for("vertex", task_tier) or cfg.vertex_model
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": cfg.temperature,
        "max_retries": 2,
    }

    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    project = cfg.vertex_project or settings.resolved_vertex_project

    if project or settings.google_application_credentials:
        kwargs["vertexai"] = True
        if project:
            kwargs["project"] = project
        kwargs["location"] = cfg.vertex_location or settings.resolved_vertex_location
    elif api_key:
        kwargs["google_api_key"] = api_key
    else:
        return None

    try:
        return ChatGoogleGenerativeAI(**kwargs)
    except Exception as exc:
        logger.warning("ChatGoogleGenerativeAI init failed: %s", exc)
        return None


def _build_legacy_vertex(cfg: Any, task_tier: TaskTier) -> Any | None:
    try:
        from langchain_google_vertexai import ChatVertexAI
    except Exception:
        return None

    model = cfg.model_for("vertex", task_tier) or cfg.vertex_model
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": cfg.temperature,
        "max_retries": 2,
    }
    if cfg.vertex_project:
        kwargs["project"] = cfg.vertex_project
    if cfg.vertex_location:
        kwargs["location"] = cfg.vertex_location
    try:
        return ChatVertexAI(**kwargs)
    except Exception as exc:
        logger.warning("ChatVertexAI init failed: %s", exc)
        return None


def _build_openai(cfg: Any, task_tier: TaskTier) -> Any | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        return None

    model = cfg.model_for("openai", task_tier) or cfg.openai_model or "gpt-4o-mini"
    try:
        return ChatOpenAI(
            model=model,
            temperature=cfg.temperature,
            timeout=cfg.timeout_seconds,
        )
    except Exception as exc:
        logger.warning("ChatOpenAI init failed: %s", exc)
        return None
