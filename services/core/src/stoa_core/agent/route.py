"""Cheap routing between tool-calling agent and RAG-only synthesis."""

from __future__ import annotations

import re
from typing import Any

from stoa_core.llm.router import invoke_json

_ROUTE_SYSTEM = """Classify whether a GTM assistant question needs multi-feature tool calls.

Return JSON: {"route": "tools" | "rag_only"}

Use "tools" when the user asks to compare across features, diagnose bottlenecks, check
competitive/campaign/alignment dashboards, orchestrate launches, or synthesize metrics
from multiple areas.

Use "rag_only" for straightforward factual questions answerable from retrieved documents,
CRM records, or a single domain (e.g. top customer, deal amounts, one competitor fact)."""

_TOOL_KEYWORDS = re.compile(
    r"\b(compare|across|misalign\w*|bottleneck|competitive intel|competitor intel|"
    r"campaign analysis|launch orchestr\w*|content production|"
    r"conversion efficiency|sales and marketing alignment|"
    r"live search|connected source|refresh\b|sync\b|"
    r"hubspot|salesforce|zendesk|gong)\b|"
    r"\bcompare\b.{0,40}\b(campaign|competitive|alignment|pipeline)\b|"
    r"\b(latest|today|this week)\b.{0,30}\b(data|pipeline|metrics)\b",
    re.IGNORECASE,
)


def requires_tools_route(question: str) -> bool:
    """Return True when keywords require bounded/full tool execution."""
    q = question.strip()
    if not q:
        return False
    return bool(_TOOL_KEYWORDS.search(q))


def classify_agent_route(
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """Return 'tools' or 'rag_only'."""
    q = question.strip()
    if not q:
        return "rag_only"

    if requires_tools_route(q):
        return "tools"

    history = history or []
    snippets = [
        f"{row.get('role', 'user')}: {str(row.get('content') or '')[:180]}"
        for row in history[-4:]
        if row.get("content")
    ]

    parsed, _provider = invoke_json(
        _ROUTE_SYSTEM,
        {"question": q, "recent_messages": snippets},
        task_name="needs_tools",
    )
    if parsed and parsed.get("route") in {"tools", "rag_only"}:
        return str(parsed["route"])
    return "rag_only"
