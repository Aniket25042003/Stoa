from __future__ import annotations

import json
from typing import Any

from stoa_core.llm.router import invoke_json, invoke_text
from stoa_core.research.types import ResearchItem


def format_research_bundle(items: list[ResearchItem], *, max_items: int = 12) -> str:
    parts: list[str] = []
    for item in items[:max_items]:
        header = f"[{item.source_type}] {item.title}"
        if item.source_url:
            header += f" ({item.source_url})"
        parts.append(f"{header}\n{item.raw_excerpt or item.summary}")
    return "\n\n".join(parts)[:45000]


def distill_company_research(
    org_name: str,
    profile_text: str,
    research_text: str,
) -> dict[str, Any]:
    schema = (
        '{"summary": "...", "products": ["..."], "positioning": "...", '
        '"target_market": "...", "competitors_mentioned": ["..."], "key_facts": ["..."]}'
    )
    parsed, _ = invoke_json(
        "Distill company web research into structured facts. Return JSON: " + schema,
        {
            "company": org_name,
            "onboarding_profile": profile_text[:8000],
            "web_research": research_text[:20000],
        },
        task_name="summarize",
    )
    if parsed:
        return parsed
    text, _ = invoke_text(
        "Summarize company research in 3-5 paragraphs with products, positioning, and market.",
        {"company": org_name, "research": research_text[:12000]},
        task_name="summarize",
    )
    return {"summary": text or "", "products": [], "positioning": "", "competitors_mentioned": []}


def distill_competitor_research(
    competitor_name: str,
    org_name: str,
    research_text: str,
) -> dict[str, Any]:
    schema = (
        '{"summary": "...", "positioning": "...", "pricing_signals": ["..."], '
        '"feature_highlights": ["..."], "threats": ["..."], "differentiators_vs_us": ["..."]}'
    )
    parsed, _ = invoke_json(
        "Distill competitor research for a marketing team. Return JSON: " + schema,
        {
            "competitor": competitor_name,
            "our_company": org_name,
            "research": research_text[:20000],
        },
        task_name="summarize",
    )
    if parsed:
        return parsed
    return {
        "summary": research_text[:2000],
        "positioning": "",
        "pricing_signals": [],
        "feature_highlights": [],
    }


def distilled_to_text(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, default=str)[:50000]
