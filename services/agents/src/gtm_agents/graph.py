from __future__ import annotations

import json
import os
import re
from typing import Any

from langgraph.graph import END, START, StateGraph

from gtm_agents.state import GTMState, ResearchItem
from gtm_agents.tools.research import merge_research, run_research_suite


def _clean(text: str | None, limit: int = 500) -> str:
    return " ".join((text or "").split())[:limit]


def _keywords(text: str, limit: int = 12) -> list[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "you",
        "your",
        "into",
        "their",
        "about",
        "startup",
        "product",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
    counts: dict[str, int] = {}
    for word in words:
        if word in stop:
            continue
        counts[word] = counts.get(word, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _research_text(state: GTMState) -> str:
    parts = []
    for item in state.get("research_items") or []:
        parts.append(f"{item.get('title', '')} {item.get('summary', '')} {item.get('raw_excerpt', '')}")
    return _clean(" ".join(parts), 8000)


def _source_refs(items: list[ResearchItem], limit: int = 12) -> list[str]:
    refs: list[str] = []
    for i, item in enumerate(items[:limit], start=1):
        title = _clean(item.get("title") or item.get("source_url") or f"Source {i}", 90)
        url = item.get("source_url") or ""
        refs.append(f"[{i}] {title} - {url}".strip())
    return refs


def _optional_llm_json(system: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Use a configured LLM for synthesis, otherwise return None.

    The model is intentionally env-driven. Set GTM_SYNTHESIS_MODEL plus the
    corresponding provider key (currently OpenAI via langchain-openai) to use it.
    """
    model = os.getenv("GTM_SYNTHESIS_MODEL")
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model, temperature=0.2)
        msg = llm.invoke(
            [
                ("system", system + "\nReturn only valid JSON."),
                ("human", json.dumps(payload, default=str)[:12000]),
            ]
        )
        content = str(getattr(msg, "content", ""))
        return json.loads(content)
    except Exception:
        return None


def node_orchestrator(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    summary = _clean(str(inp.get("product_description") or inp.get("summary") or ""), 1200)
    product_name = _clean(str(inp.get("product_name") or ""), 120)
    target = _clean(str(inp.get("target_customers") or ""), 240)
    geography = _clean(str(inp.get("geography") or ""), 120)
    competitors = ", ".join(inp.get("known_competitors") or []) if isinstance(inp.get("known_competitors"), list) else _clean(str(inp.get("known_competitors") or ""), 240)
    category_terms = " ".join(_keywords(f"{product_name} {summary} {target}"))
    base = " ".join(part for part in (product_name, category_terms, target, geography) if part).strip()
    plan = {
        "product_name": product_name,
        "product_summary": summary,
        "target_customers": target,
        "geography": geography,
        "known_competitors": competitors,
        "objectives": ["voice_of_customer", "competitive_landscape", "icp_hypotheses", "positioning", "channel_experiments"],
        "constraints": inp.get("constraints") or [],
        "horizon_days": inp.get("horizon_days") or 90,
        "queries": {
            "reddit": [f"{base} pain points alternatives recommendations".strip()],
            "x": [f"{base} complaints launch feedback".strip()],
            "web": [f"{base} market competitors customer pain points pricing".strip()],
            "competitors": [f"{base} competitors alternatives pricing comparison {competitors}".strip()],
        },
    }
    return {"research_plan": plan}


def node_research(state: GTMState) -> dict[str, Any]:
    plan = state.get("research_plan") or {}
    result = run_research_suite(plan)
    items = result["items"]
    bundle = merge_research(items)
    return {"research_items": items, "research_bundle": bundle, "tool_errors": result["warnings"]}


def node_segmentation(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    bundle = state.get("research_bundle") or {}
    research_text = _research_text(state)
    kw = _keywords(f"{inp.get('product_description', '')} {research_text}")
    target = _clean(str(inp.get("target_customers") or "teams actively experiencing the core problem described by the founder"), 180)
    evidence = bundle.get("theme_counts") or {}
    primary_triggers = [k for k, _ in sorted(evidence.items(), key=lambda kv: -kv[1])[:5]]
    if not primary_triggers:
        primary_triggers = kw[:5] or ["manual workflow pain", "unclear ROI", "tool fragmentation"]
    llm = _optional_llm_json(
        "You are a senior GTM strategist. Create ICP and persona segmentation from the founder input and research evidence.",
        {"input": inp, "research_items": state.get("research_items") or [], "theme_counts": evidence},
    )
    if llm:
        return {"segmentation": llm}
    return {
        "segmentation": {
            "icps": [
                {
                    "name": f"Primary ICP: {target}",
                    "signals": primary_triggers,
                    "confidence": "medium" if bundle.get("count", 0) >= 5 else "low",
                }
            ],
            "personas": [
                {
                    "role": "Economic buyer",
                    "jobs": ["justify spend", "reduce GTM risk", "choose launch channel"],
                    "likely_titles": ["Founder", "Head of Growth", "VP Marketing"],
                },
                {
                    "role": "Daily user",
                    "jobs": ["collect research", "turn findings into messaging", "track experiments"],
                    "likely_titles": ["PMM", "Growth marketer", "RevOps"],
                },
            ],
            "notes": f"Synthesized from {bundle.get('count', 0)} collected research sources and the founder input.",
        }
    }


def node_positioning(state: GTMState) -> dict[str, Any]:
    inp = state.get("input") or {}
    research_text = _research_text(state)
    kw = _keywords(f"{inp.get('product_description', '')} {research_text}", limit=8)
    problem = _clean(str(inp.get("product_description") or ""), 220)
    source_count = len(state.get("research_items") or [])
    llm = _optional_llm_json(
        "You are a product marketing strategist. Produce positioning, value props, objections, proof points, and messaging angles.",
        {"input": inp, "research_items": state.get("research_items") or [], "segmentation": state.get("segmentation") or {}},
    )
    if llm:
        return {"positioning": llm}
    return {
        "positioning": {
            "core_narrative": f"For teams dealing with {', '.join(kw[:3]) or 'market uncertainty'}, this product should be framed around a concrete before/after outcome: {problem}",
            "value_props": [
                f"Turns scattered GTM signals into a prioritized plan backed by {source_count} collected source(s).",
                "Reduces launch uncertainty by linking ICP, messaging, and channel choices to evidence.",
                "Creates experiment-ready assets instead of stopping at generic strategy recommendations.",
            ],
            "messaging_angles": [
                {"angle": "Evidence-backed launch strategy", "tone": "analytical, credible", "proof_needed": "source citations and experiment metrics"},
                {"angle": "Founder-speed market learning", "tone": "direct, pragmatic", "proof_needed": "time saved versus manual research"},
                {"angle": "From customer voice to channel plan", "tone": "operator-focused", "proof_needed": "before/after workflow demo"},
            ],
        }
    }


def node_channels(state: GTMState) -> dict[str, Any]:
    by_type = (state.get("research_bundle") or {}).get("by_type") or {}
    counts = {k: len(v) for k, v in by_type.items()}
    total = sum(counts.values()) or 1
    ranked = [
        {
            "channel": "Community research and launch posts",
            "score": round((counts.get("reddit", 0) + counts.get("x", 0)) / total, 2),
            "rationale": "Use when Reddit/X voice-of-customer evidence is strong.",
        },
        {
            "channel": "SEO and comparison content",
            "score": round((counts.get("web", 0) + counts.get("serp", 0)) / total, 2),
            "rationale": "Use when web and competitor pages reveal category search demand.",
        },
        {
            "channel": "Founder-led outbound",
            "score": 0.5 if counts.get("serp", 0) else 0.35,
            "rationale": "Use to validate ICP and positioning quickly with direct buyer conversations.",
        },
    ]
    ranked = sorted(ranked, key=lambda row: row["score"], reverse=True)
    llm = _optional_llm_json(
        "You are a growth strategist. Rank launch channels and design measurable GTM experiments from the evidence.",
        {"input": state.get("input") or {}, "research_bundle": state.get("research_bundle") or {}, "positioning": state.get("positioning") or {}},
    )
    if llm:
        return {"channels": llm}
    return {
        "channels": {
            "ranked": ranked,
            "experiments": [
                {"name": "Landing-page angle test", "metric": "visitor-to-qualified-lead conversion", "effort": "S"},
                {"name": "Founder-led message test", "metric": "positive reply rate", "effort": "S"},
                {"name": "Community post / discussion test", "metric": "qualified conversations started", "effort": "M"},
            ],
        }
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
    md = f"""# GTM Strategy - {title}

## Executive summary
This document synthesizes founder input and collected market signals into a launch-ready GTM plan.
Research confidence: **{report_confidence}**.

## Product & problem
{inp.get("product_description", "No product description provided.")}

## ICP & personas
```json
{json.dumps(seg, indent=2)}
```

## Positioning & messaging
```json
{json.dumps(pos, indent=2)}
```

## Channel strategy & experiments
```json
{json.dumps(ch, indent=2)}
```

## 30 / 60 / 90-day plan
- **30 days:** validate ICP and top two messaging angles with direct buyer conversations and one landing-page test.
- **60 days:** double down on the best-performing channel, publish evidence-backed content, and build sales enablement from customer language.
- **90 days:** scale the winning motion with a repeatable weekly experiment cadence and source-backed channel scorecard.

## Risks & assumptions
{chr(10).join(f"- {w}" for w in warnings) if warnings else "- External research ran without integration warnings."}
- Messaging still requires customer validation through the proposed experiments.

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
