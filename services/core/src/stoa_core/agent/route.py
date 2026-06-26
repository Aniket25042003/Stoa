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
    r"(compare|across|alignment|misalign\w*|bottleneck|competitive|competitor|"
    r"campaign analysis|launch orchestr|content production|pipeline|funnel|"
    r"channels?|conversion efficiency|sales and marketing)",
    re.IGNORECASE,
)


def classify_agent_route(
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
) -> str:
    """Return 'tools' or 'rag_only'."""
    q = question.strip()
    if not q:
        return "rag_only"

    if _TOOL_KEYWORDS.search(q):
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
