from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from gtm_agents.state import GTMState, ResearchItem
from gtm_agents.autonomy import autonomous_research, synthesize_report_markdown, synthesize_section


def _clean(text: str | None, limit: int = 500) -> str:
    return " ".join((text or "").split())[:limit]


def _source_refs(items: list[ResearchItem], limit: int = 12) -> list[str]:
    refs: list[str] = []
    for i, item in enumerate(items[:limit], start=1):
        title = _clean(item.get("title") or item.get("source_url") or f"Source {i}", 90)
        url = item.get("source_url") or ""
        refs.append(f"[{i}] {title} - {url}".strip())
    return refs


def node_orchestrator(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    plan = {
        "role": "autonomous_research_supervisor",
        "instruction": "List MCP tools, decide which are relevant for this product, then call only those tools.",
        "founder_input": inp,
    }
    return {"research_plan": plan}


def node_research(state: GTMState) -> dict[str, Any]:
    result = autonomous_research(state.get("input") or {})
    return {
        "research_plan": result["research_plan"],
        "research_items": result["items"],
        "research_bundle": result["research_bundle"],
        "tool_results": result["tool_results"],
        "tool_errors": result["warnings"],
    }


def node_segmentation(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    research = {"items": state.get("research_items") or [], "bundle": state.get("research_bundle") or {}, "plan": state.get("research_plan") or {}}
    return {"segmentation": synthesize_section("segmentation", inp, research)}


def node_positioning(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    research = {"items": state.get("research_items") or [], "bundle": state.get("research_bundle") or {}, "plan": state.get("research_plan") or {}}
    return {"positioning": synthesize_section("positioning_and_messaging", inp, research, prior={"segmentation": state.get("segmentation") or {}})}


def node_channels(state: GTMState) -> dict[str, Any]:
    research = {"items": state.get("research_items") or [], "bundle": state.get("research_bundle") or {}, "plan": state.get("research_plan") or {}}
    return {"channels": synthesize_section("channel_strategy_and_experiments", state.get("input") or {}, research, prior={"segmentation": state.get("segmentation") or {}, "positioning": state.get("positioning") or {}})}


def node_validate(state: GTMState) -> dict[str, Any]:
    items = state.get("research_items") or []
    warnings = list(state.get("tool_errors") or [])
    checks = {
        "has_founder_input": bool((state.get("input") or {}).get("product_description")),
        "has_external_sources": bool(items),
        "has_citations": any(item.get("source_url") for item in items),
        "warnings": warnings,
    }
    return {"validation": checks}


def node_writer(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    title = inp.get("product_name") or "Unnamed product"
    seg = state.get("segmentation") or {}
    pos = state.get("positioning") or {}
    ch = state.get("channels") or {}
    validation = state.get("validation") or {}
    items = state.get("research_items") or []
    refs = _source_refs(items)
    warnings = validation.get("warnings") or []
    report_confidence = "medium" if validation.get("has_external_sources") else "low"
    research = {
        "items": items,
        "bundle": state.get("research_bundle") or {},
        "plan": state.get("research_plan") or {},
        "warnings": warnings,
    }
    synthesis = {"segmentation": seg, "positioning": pos, "channels": ch, "validation": validation}
    autonomous_md = synthesize_report_markdown(inp, research, synthesis)
    if autonomous_md:
        return {"final_markdown": autonomous_md}
    md = f"""# GTM Strategy - {title}

## Executive summary
This document synthesizes founder input and collected market signals into an evidence-backed GTM plan.
Research confidence: **{report_confidence}**.

## Product & problem
{inp.get("product_description", "No product description provided.")}

## Autonomous synthesis: segmentation
```json
{json.dumps(seg, indent=2)}
```

## Autonomous synthesis: positioning and messaging
```json
{json.dumps(pos, indent=2)}
```

## Autonomous synthesis: channel strategy and experiments
```json
{json.dumps(ch, indent=2)}
```

## Risks & assumptions
{chr(10).join(f"- {w}" for w in warnings) if warnings else "- External research ran without integration warnings."}
- Configure `GTM_AGENT_MODEL` and `OPENAI_API_KEY` for fully autonomous long-form strategy writing.

## Appendix
### Sources
{chr(10).join(f"- {ref}" for ref in refs) if refs else "- No external sources were collected. Configure Tavily/Reddit/X/SerpAPI credentials or allow Jina egress, then rerun."}

### Validation
```json
{json.dumps(validation, indent=2)}
```
"""
    return {"final_markdown": md}


def build_graph() -> Any:
    g = StateGraph(GTMState)
    g.add_node("orchestrator", node_orchestrator)
    g.add_node("research", node_research)
    g.add_node("segmentation", node_segmentation)
    g.add_node("positioning", node_positioning)
    g.add_node("channels", node_channels)
    g.add_node("validate", node_validate)
    g.add_node("writer", node_writer)

    g.add_edge(START, "orchestrator")
    g.add_edge("orchestrator", "research")
    g.add_edge("research", "segmentation")
    g.add_edge("segmentation", "positioning")
    g.add_edge("positioning", "channels")
    g.add_edge("channels", "validate")
    g.add_edge("validate", "writer")
    g.add_edge("writer", END)
    return g.compile()


def run_pipeline(initial: GTMState) -> GTMState:
    app = build_graph()
    out = app.invoke(initial)
    return out  # type: ignore[return-value]
