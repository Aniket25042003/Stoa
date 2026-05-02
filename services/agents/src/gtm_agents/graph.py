from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from gtm_agents.state import GTMState, ResearchItem
from gtm_agents.autonomy import (
    autonomous_research,
    complete_step,
    create_agent_plan,
    request_fix,
    run_reasoning_layer,
    run_writing_layer,
)
from gtm_agents.memory import append_memory, read_memory, write_context_snapshot


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
    run_id = state.get("run_id")
    plan = create_agent_plan(
        "main_agent",
        "Create and supervise the full GTM workflow across research, reasoning, and writing. Gate each layer before the next starts.",
        {"founder_input": inp},
        [
            "Understand the founder input and success criteria.",
            "Instruct and supervise the research parent agent.",
            "Approve research before reasoning begins.",
            "Instruct and supervise the reasoning parent agent.",
            "Approve reasoning before writing begins.",
            "Instruct and supervise the writing parent agent.",
            "Final-review the complete GTM report before marking the run done.",
        ],
        run_id,
        None,
    )
    write_context_snapshot(run_id, {"master_plan": plan, "input": inp})
    return {"master_plan": plan, "memory_context": read_memory(run_id, 25)}


def node_research(state: GTMState) -> dict[str, Any]:
    result = autonomous_research(state.get("input") or {}, state.get("run_id"), "main_agent")
    master_plan = state.get("master_plan") or {}
    if result.get("research_parent_approval", {}).get("approved"):
        complete_step(master_plan, 1, "Research parent completed its plan.")
        complete_step(master_plan, 2, "Main agent approved research layer.")
    else:
        request_fix(master_plan, "Research layer did not receive approval.")
        raise RuntimeError("Main agent rejected research layer; stopping before reasoning.")
    return {
        "master_plan": master_plan,
        "research_plan": result["research_plan"],
        "research_items": result["items"],
        "research_bundle": result["research_bundle"],
        "tool_results": result["tool_results"],
        "tool_errors": result["warnings"],
        "agent_plans": {"research_parent": result.get("research_parent_plan")},
        "approvals": {"research_parent": result.get("research_parent_approval")},
        "memory_context": read_memory(state.get("run_id"), 50),
    }


def node_reasoning(state: GTMState) -> dict[str, Any]:
    research = {"items": state.get("research_items") or [], "bundle": state.get("research_bundle") or {}, "plan": state.get("research_plan") or {}}
    result = run_reasoning_layer(state.get("input") or {}, research, state.get("run_id"), "main_agent")
    master_plan = state.get("master_plan") or {}
    if result.get("reasoning_parent_approval", {}).get("approved"):
        complete_step(master_plan, 3, "Reasoning parent completed its plan.")
        complete_step(master_plan, 4, "Main agent approved reasoning layer.")
    else:
        request_fix(master_plan, "Reasoning layer did not receive approval.")
        raise RuntimeError("Main agent rejected reasoning layer; stopping before writing.")
    plans = dict(state.get("agent_plans") or {})
    plans["reasoning_parent"] = result.get("reasoning_parent_plan")
    approvals = dict(state.get("approvals") or {})
    approvals["reasoning_parent"] = result.get("reasoning_parent_approval")
    return {
        "master_plan": master_plan,
        "segmentation": result.get("segmentation") or {},
        "positioning": result.get("positioning") or {},
        "channels": result.get("channels") or {},
        "agent_plans": plans,
        "approvals": approvals,
        "memory_context": read_memory(state.get("run_id"), 50),
    }


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

    def _fallback_markdown() -> str:
        return f"""# GTM Strategy - {title}

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

    result = run_writing_layer(inp, research, synthesis, validation, _fallback_markdown, state.get("run_id"), "main_agent")
    master_plan = state.get("master_plan") or {}
    if result.get("writing_parent_approval", {}).get("approved"):
        complete_step(master_plan, 5, "Writing parent completed its plan.")
        complete_step(master_plan, 6, "Main agent approved final GTM report.")
        master_plan["status"] = "completed"
    else:
        request_fix(master_plan, "Writing layer did not receive final approval.")
        raise RuntimeError("Main agent rejected writing layer; run requires revision.")
    append_memory(state.get("run_id"), "main_agent", "final_review", {"master_plan": master_plan, "writing_approval": result.get("writing_parent_approval")})
    plans = dict(state.get("agent_plans") or {})
    plans["writing_parent"] = result.get("writing_parent_plan")
    approvals = dict(state.get("approvals") or {})
    approvals["writing_parent"] = result.get("writing_parent_approval")
    return {
        "master_plan": master_plan,
        "agent_plans": plans,
        "approvals": approvals,
        "final_markdown": result.get("markdown") or "",
        "memory_context": read_memory(state.get("run_id"), 50),
    }


def build_graph() -> Any:
    g = StateGraph(GTMState)
    g.add_node("orchestrator", node_orchestrator)
    g.add_node("research", node_research)
    g.add_node("reasoning", node_reasoning)
    g.add_node("validate", node_validate)
    g.add_node("writer", node_writer)

    g.add_edge(START, "orchestrator")
    g.add_edge("orchestrator", "research")
    g.add_edge("research", "reasoning")
    g.add_edge("reasoning", "validate")
    g.add_edge("validate", "writer")
    g.add_edge("writer", END)
    return g.compile()


def run_pipeline(initial: GTMState) -> GTMState:
    app = build_graph()
    out = app.invoke(initial)
    return out  # type: ignore[return-value]
