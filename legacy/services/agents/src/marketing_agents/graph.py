"""LangGraph: one marketing chat turn — route → specialists → critic → finalize → memory."""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from marketing_agents.state import MarketingTurnState
from marketing_agents.subagents import (
    run_brand_voice_keeper,
    run_channel_planner,
    run_competitor_intel,
    run_copywriter,
    run_critic,
    run_finalize_reply,
    run_idea_generator,
    run_memory_curator,
    run_router,
    run_marketing_strategist,
    run_scriptwriter,
)
from marketing_agents.vertex_media import generate_image, generate_video
from shared_memory.kb import kb_facts, kb_format_for_prompt, kb_search


def _progress(state: MarketingTurnState, agent: str, phase: str, message: str, detail: dict[str, Any] | None = None) -> None:
    cb = state.get("progress_callback")
    if callable(cb):
        try:
            cb(agent, phase, message, detail or {})
        except Exception:
            pass


def node_load_context(state: MarketingTurnState) -> dict[str, Any]:
    cid = state.get("company_id") or ""
    um = state.get("user_message") or ""
    _progress(state, "main_marketing_agent", "context", "Loading company knowledge base")
    rows: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    if cid:
        try:
            rows = kb_search(cid, um, k=10)
        except Exception:
            rows = []
        try:
            facts = kb_facts(cid, limit=20)
        except Exception:
            facts = []
    merged = rows + [f for f in facts if f.get("id") not in {r.get("id") for r in rows}]
    kb_ctx = kb_format_for_prompt(merged[:25], max_chars=14000)
    return {"kb_context": kb_ctx}


def node_route(state: MarketingTurnState) -> dict[str, Any]:
    route = run_router(state.get("user_message") or "", state.get("kb_context") or "", progress=state.get("progress_callback"))
    return {"routed_agents": route.get("agents") or [], "routing_rationale": route.get("rationale") or ""}


def node_run_specialists(state: MarketingTurnState) -> dict[str, Any]:
    cid = state.get("company_id") or ""
    um = state.get("user_message") or ""
    kb = state.get("kb_context") or ""
    agents = list(state.get("routed_agents") or [])
    outputs: dict[str, Any] = {}
    progress = state.get("progress_callback")

    strategist: dict[str, Any] = {}
    ideas: dict[str, Any] = {}

    for name in agents:
        if name == "marketing_strategist":
            strategist = run_marketing_strategist(cid, um, kb, progress=progress)
            outputs["marketing_strategist"] = strategist
        elif name == "competitor_intel":
            outputs["competitor_intel"] = run_competitor_intel(cid, um, kb, progress=progress)
        elif name == "idea_generator":
            ideas = run_idea_generator(cid, um, kb, strategist or outputs.get("marketing_strategist") or {}, progress=progress)
            outputs["idea_generator"] = ideas
        elif name == "copywriter":
            if not ideas and "idea_generator" in outputs:
                ideas = outputs.get("idea_generator") or {}
            if not ideas:
                ideas = run_idea_generator(cid, um, kb, outputs.get("marketing_strategist") or {}, progress=progress)
                outputs["idea_generator"] = ideas
            outputs["copywriter"] = run_copywriter(um, kb, ideas, progress=progress)
        elif name == "scriptwriter":
            if not ideas:
                ideas = outputs.get("idea_generator") or run_idea_generator(cid, um, kb, outputs.get("marketing_strategist") or {}, progress=progress)
                outputs.setdefault("idea_generator", ideas)
            outputs["scriptwriter"] = run_scriptwriter(um, kb, ideas, progress=progress)
        elif name == "channel_planner":
            if not ideas:
                ideas = outputs.get("idea_generator") or {}
            outputs["channel_planner"] = run_channel_planner(kb, ideas, progress=progress)
        elif name == "brand_voice_keeper":
            outputs["brand_voice_keeper"] = run_brand_voice_keeper(
                kb,
                {k: v for k, v in outputs.items() if k in ("copywriter", "scriptwriter", "idea_generator")},
                progress=progress,
            )
        elif name == "image_generator":
            prompt = um[:500] if um else "Product hero image, clean modern SaaS marketing style"
            chat_id = state.get("chat_id") or ""
            img = generate_image(company_id=cid, chat_id=chat_id, prompt=prompt)
            outputs["image_generator"] = img
        elif name == "video_generator":
            vid = generate_video(company_id=cid, chat_id=state.get("chat_id") or "", prompt=um[:500] or "Product demo clip")
            outputs["video_generator"] = vid

    if not ideas and "idea_generator" not in outputs and any(a in agents for a in ("copywriter", "scriptwriter", "channel_planner")):
        ideas = run_idea_generator(cid, um, kb, outputs.get("marketing_strategist") or {}, progress=progress)
        outputs["idea_generator"] = ideas

    draft = json.dumps(outputs, indent=2, default=str)[:12000]
    return {"agent_outputs": outputs, "draft": draft}


def node_critic(state: MarketingTurnState) -> dict[str, Any]:
    cr = run_critic(
        state.get("user_message") or "",
        state.get("kb_context") or "",
        state.get("draft") or "",
        progress=state.get("progress_callback"),
    )
    return {"critic_ok": cr.get("approved", True), "critic_feedback": cr.get("feedback") or ""}


def node_finalize(state: MarketingTurnState) -> dict[str, Any]:
    reply = run_finalize_reply(
        state.get("user_message") or "",
        state.get("kb_context") or "",
        state.get("agent_outputs") or {},
        progress=state.get("progress_callback"),
    )
    if not state.get("critic_ok", True):
        reply = f"{reply}\n\n---\n*Internal review note:* {state.get('critic_feedback', '')}"
    return {"final_reply": reply}


def node_curator(state: MarketingTurnState) -> dict[str, Any]:
    run_memory_curator(
        state.get("company_id") or "",
        state.get("chat_id") or "",
        state.get("user_message") or "",
        state.get("final_reply") or "",
        state.get("agent_outputs") or {},
        progress=state.get("progress_callback"),
    )
    return {}


def build_marketing_turn_graph() -> Any:
    g = StateGraph(MarketingTurnState)
    g.add_node("load_context", node_load_context)
    g.add_node("route", node_route)
    g.add_node("specialists", node_run_specialists)
    g.add_node("critic", node_critic)
    g.add_node("finalize", node_finalize)
    g.add_node("curator", node_curator)

    g.add_edge(START, "load_context")
    g.add_edge("load_context", "route")
    g.add_edge("route", "specialists")
    g.add_edge("specialists", "critic")
    g.add_edge("critic", "finalize")
    g.add_edge("finalize", "curator")
    g.add_edge("curator", END)
    return g.compile()


def run_marketing_turn(initial: MarketingTurnState) -> MarketingTurnState:
    app = build_marketing_turn_graph()
    return app.invoke(initial)  # type: ignore[return-value]
