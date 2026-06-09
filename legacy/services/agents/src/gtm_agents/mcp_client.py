from __future__ import annotations

from typing import Any, Callable

from gtm_agents.observability import span
from gtm_agents.tools import crawl_search_results, crawl_web, research_competitors, research_web, run_research_suite
from gtm_agents.tools.research import research_plan

ToolFn = Callable[..., dict[str, Any]]


def _tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    fn: ToolFn,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "fn": fn,
    }


_DIRECT_TOOLS: dict[str, dict[str, Any]] = {
    "crawl_web": _tool(
        "crawl_web",
        "Deep-read specific URLs with Playwright when you already have high-value pages.",
        {
            "type": "object",
            "properties": {
                "start_urls": {"type": "array", "items": {"type": "string"}},
                "keywords": {"type": "string"},
                "max_pages": {"type": "integer"},
                "max_depth": {"type": "integer"},
                "same_domain_only": {"type": "boolean"},
                "include_url_patterns": {"type": "array", "items": {"type": "string"}},
                "exclude_url_patterns": {"type": "array", "items": {"type": "string"}},
                "respect_robots": {"type": "boolean"},
                "product_context": {"type": "string"},
            },
            "required": ["start_urls"],
        },
        crawl_web,
    ),
    "crawl_search_results": _tool(
        "crawl_search_results",
        "Discover open-web URLs via search, then crawl the top hits with Playwright.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"},
                "max_pages_per_result": {"type": "integer"},
                "max_depth": {"type": "integer"},
                "product_context": {"type": "string"},
            },
            "required": ["query"],
        },
        crawl_search_results,
    ),
    "web_research": _tool(
        "web_research",
        "Search the open web for market evidence, docs, landing pages, reports, and reviews.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "product_context": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
        lambda query, product_context="", max_results=8: research_web(
            research_plan("web", query, product_context),
            max_results=max_results,
        ),
    ),
    "competitor_research": _tool(
        "competitor_research",
        "Discover competitors, alternatives, comparison pages, and pricing signals.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "product_context": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
        lambda query, product_context="", max_results=8: research_competitors(
            research_plan("competitors", query, product_context),
            max_results=max_results,
        ),
    ),
    "full_research_suite": _tool(
        "full_research_suite",
        "Run the complete research suite when broad coverage matters more than selective tool choice.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "product_context": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
        lambda query, product_context="", max_results=8: run_research_suite(
            {
                "product_summary": product_context or query,
                "queries": {
                    "web": [query],
                    "competitors": [query],
                },
            }
        ),
    ),
}


def list_research_tools() -> list[dict[str, Any]]:
    with span("research_list_tools", "tool", {"tool_count": len(_DIRECT_TOOLS)}):
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in _DIRECT_TOOLS.values()
        ]


def _normalize_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"items": raw, "warnings": []}
    return {"items": [], "warnings": [f"Research tool returned unsupported result type: {type(raw).__name__}"]}


def call_research_tools(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for call in calls:
        name = str(call.get("tool_name") or call.get("name") or "")
        arguments = call.get("arguments") or {}
        if not name:
            results.append({"items": [], "warnings": ["Skipped research call without tool_name."], "tool_name": name})
            continue
        tool = _DIRECT_TOOLS.get(name)
        if tool is None:
            results.append(
                {
                    "items": [],
                    "warnings": [f"Unknown research tool: {name}"],
                    "tool_name": name,
                    "arguments": arguments,
                    "reason": call.get("reason"),
                }
            )
            continue
        try:
            with span(
                "research_call_tool",
                "tool",
                {
                    "tool_name": name,
                    "argument_keys": list(arguments.keys()) if isinstance(arguments, dict) else [],
                    "reason": call.get("reason"),
                },
            ):
                raw = tool["fn"](**arguments)
            parsed = _normalize_result(raw)
            parsed["tool_name"] = name
            parsed["arguments"] = arguments
            parsed["reason"] = call.get("reason")
            results.append(parsed)
        except Exception as e:
            results.append(
                {
                    "items": [],
                    "warnings": [f"Research tool {name} failed: {e}"],
                    "tool_name": name,
                    "arguments": arguments,
                    "reason": call.get("reason"),
                }
            )
    return results
