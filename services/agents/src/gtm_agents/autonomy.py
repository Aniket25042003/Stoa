from __future__ import annotations

import json
import os
from typing import Any

from gtm_agents.mcp_client import call_research_tools, list_research_tools
from gtm_agents.state import ResearchItem
from gtm_agents.tools.research import merge_research


def _llm_json(system: str, payload: dict[str, Any], max_chars: int = 16000) -> dict[str, Any] | None:
    model = os.getenv("GTM_AGENT_MODEL") or os.getenv("GTM_SYNTHESIS_MODEL")
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model, temperature=0.25)
        msg = llm.invoke(
            [
                ("system", system + "\nReturn only valid JSON. Do not wrap it in markdown."),
                ("human", json.dumps(payload, default=str)[:max_chars]),
            ]
        )
        content = str(getattr(msg, "content", "")).strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.removeprefix("json").strip()
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _product_context(user_input: dict[str, Any]) -> str:
    fields = [
        ("Product", user_input.get("product_name")),
        ("Description", user_input.get("product_description")),
        ("Website", user_input.get("website_url")),
        ("Target customers", user_input.get("target_customers")),
        ("Geography", user_input.get("geography")),
        ("Business model", user_input.get("business_model")),
        ("Stage", user_input.get("stage")),
        ("Known competitors", user_input.get("known_competitors")),
        ("Constraints", user_input.get("constraints")),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


def _fallback_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Minimal non-LLM fallback: choose broad web research only.

    This keeps tests/local runs deterministic without pretending to be an
    autonomous strategist. Real autonomy requires GTM_AGENT_MODEL.
    """
    available = {tool["name"] for tool in tools}
    query = " ".join(
        str(v)
        for v in (
            user_input.get("product_name"),
            user_input.get("product_description"),
            user_input.get("target_customers"),
            "market competitors customer pain points pricing",
        )
        if v
    )
    calls: list[dict[str, Any]] = []
    if "web_research" in available:
        calls.append(
            {
                "tool_name": "web_research",
                "arguments": {"query": query[:500], "product_context": _product_context(user_input), "max_results": 8},
                "reason": "Fallback path: broad open-web evidence is most generally useful across product types.",
            }
        )
    return calls


def plan_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = """You are the autonomous research supervisor for a GTM multi-agent system.
Choose only the MCP tools that are likely to produce useful evidence for this specific product.
Do not call every tool by default. For example:
- Internet/software/devtools products may justify Reddit, X, web, and competitor search.
- Physical products, food, local services, healthcare, or regulated categories may rely more on web/competitor research.
- Use social/forum tools only when the target buyers likely discuss this category there.
Create focused, source-specific queries. Return:
{
  "research_strategy": "short rationale",
  "calls": [
    {"tool_name": "...", "arguments": {"query": "...", "product_context": "...", "max_results": 5}, "reason": "..."}
  ],
  "skipped_tools": [{"tool_name": "...", "reason": "..."}]
}
"""
    planned = _llm_json(prompt, {"user_input": user_input, "available_tools": tools})
    if planned and isinstance(planned.get("calls"), list):
        planned["autonomy_mode"] = "llm"
        return planned
    return {
        "autonomy_mode": "fallback",
        "research_strategy": "No GTM_AGENT_MODEL/OPENAI_API_KEY configured; using conservative broad web research fallback.",
        "calls": _fallback_research_calls(user_input, tools),
        "skipped_tools": [{"tool_name": "llm_planner", "reason": "Autonomous LLM planner not configured."}],
    }


def autonomous_research(user_input: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("GTM_DISABLE_EXTERNAL_RESEARCH") == "true":
        return {
            "research_plan": {
                "autonomy_mode": "disabled",
                "research_strategy": "External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true.",
                "calls": [],
                "skipped_tools": [],
            },
            "items": [],
            "warnings": ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."],
            "tool_results": [],
            "research_bundle": merge_research([]),
        }

    try:
        tools = list_research_tools()
    except Exception as e:
        return {
            "research_plan": {"autonomy_mode": "error", "research_strategy": "Could not list MCP research tools.", "calls": []},
            "items": [],
            "warnings": [f"MCP research server unavailable: {e}"],
            "tool_results": [],
            "research_bundle": merge_research([]),
        }

    research_plan = plan_research_calls(user_input, tools)
    tool_results = call_research_tools(research_plan.get("calls") or [])
    items: list[ResearchItem] = []
    warnings: list[str] = []
    for result in tool_results:
        items.extend(result.get("items") or [])
        warnings.extend(result.get("warnings") or [])
    return {
        "research_plan": research_plan,
        "items": items,
        "warnings": warnings,
        "tool_results": tool_results,
        "research_bundle": merge_research(items),
    }


def synthesize_section(section_name: str, user_input: dict[str, Any], research: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    prompt = f"""You are a senior GTM agent responsible for the {section_name} layer.
You have full freedom to choose the structure and fields that are most useful for this product.
Do not force generic keys like value_props or messaging_angles unless they genuinely fit the evidence.
Ground every important claim in the provided evidence. If evidence is thin, say so explicitly.
Return a JSON object with your chosen structure."""
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "prior": prior or {}})
    if llm:
        return llm

    # Non-LLM fallback stays evidence-derived and avoids fixed GTM strategy values.
    items = research.get("items") or []
    return {
        "mode": "fallback_without_llm",
        "section": section_name,
        "evidence_count": len(items),
        "evidence_summary": [item.get("summary") or item.get("title") for item in items[:5]],
        "next_step": f"Configure GTM_AGENT_MODEL and OPENAI_API_KEY for autonomous {section_name} synthesis.",
    }


def synthesize_report_markdown(user_input: dict[str, Any], research: dict[str, Any], synthesis: dict[str, Any]) -> str | None:
    prompt = """You are the final WriterAgent for an autonomous GTM system.
Write a professional GTM strategy document in Markdown. You may decide the section structure,
but it must include citations/source references where available, assumptions, and concrete next actions.
Do not use a generic template if the product calls for a different structure."""
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "synthesis": synthesis}, max_chars=24000)
    if not llm:
        return None
    markdown = llm.get("markdown") or llm.get("report") or llm.get("content")
    return str(markdown) if markdown else None
