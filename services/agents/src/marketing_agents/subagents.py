"""LLM-driven subagent steps (text). Image/video via vertex_media tools."""

from __future__ import annotations

import json
from typing import Any, Callable

from gtm_agents.llm import invoke_json


def _emit(
    cb: Callable[..., None] | None,
    agent: str,
    phase: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> None:
    if cb:
        try:
            cb(agent, phase, message, detail or {})
        except Exception:
            pass


def run_marketing_strategist(
    company_id: str,
    user_message: str,
    kb_context: str,
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "marketing_strategist", "planning", "Bootstrapping marketing playbook from KB + ask")
    system = """You are a senior marketing strategist. Given company KB context and the user ask, output JSON:
{"playbook_summary": "string", "priorities": ["string"], "constraints": ["string"]}"""
    payload = {"company_id": company_id, "kb_context": kb_context[:20000], "user_message": user_message[:8000]}
    parsed, _ = invoke_json(system, payload, task_tier="premium")
    return parsed or {"playbook_summary": "", "priorities": [], "constraints": []}


def run_idea_generator(
    company_id: str,
    user_message: str,
    kb_context: str,
    strategist: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "idea_generator", "ideas", "Generating campaign concepts")
    system = """You are a creative marketer. Output JSON:
{"ideas": [{"title": "string", "hook": "string", "channels": ["string"], "rationale": "string"}]} (3-5 ideas). Ground in KB; cite competitor angles where relevant."""
    payload = {
        "company_id": company_id,
        "kb_context": kb_context[:20000],
        "user_message": user_message[:8000],
        "strategist": strategist,
    }
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    return parsed or {"ideas": []}


def run_copywriter(
    user_message: str,
    kb_context: str,
    ideas: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "copywriter", "copy", "Drafting ad/social copy variants")
    system = """Output JSON: {"copy_variants": [{"label": "string", "body": "string", "format": "meta_ad|linkedin_post|tweet|email"}]}"""
    payload = {"user_message": user_message[:8000], "kb_context": kb_context[:12000], "ideas": ideas}
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    return parsed or {"copy_variants": []}


def run_scriptwriter(
    user_message: str,
    kb_context: str,
    ideas: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "scriptwriter", "script", "Writing video/podcast script outline")
    system = """Output JSON: {"script": "markdown string with beats and VO lines", "format": "short_form|long_form"}"""
    payload = {"user_message": user_message[:8000], "kb_context": kb_context[:12000], "ideas": ideas}
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    return parsed or {"script": "", "format": "short_form"}


def run_brand_voice_keeper(
    kb_context: str,
    draft_snippets: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "brand_voice_keeper", "review", "Checking brand voice alignment")
    system = """Output JSON: {"aligned": true|false, "fixes": ["string"], "tone_notes": "string"}"""
    payload = {"kb_context": kb_context[:8000], "drafts": draft_snippets}
    parsed, _ = invoke_json(system, payload, task_tier="cheap")
    return parsed or {"aligned": True, "fixes": [], "tone_notes": ""}


def run_competitor_intel(
    company_id: str,
    user_message: str,
    kb_context: str,
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "competitor_intel", "research", "Synthesizing competitor signals from KB (no live crawl in worker stub)")
    system = """Output JSON: {"summary": "string", "what_worked": ["string"], "gaps": ["string"]} based only on kb_context."""
    payload = {"company_id": company_id, "user_message": user_message[:4000], "kb_context": kb_context[:16000]}
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    return parsed or {"summary": "", "what_worked": [], "gaps": []}


def run_channel_planner(
    kb_context: str,
    ideas: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "channel_planner", "calendar", "Building 2-week channel cadence sketch")
    system = """Output JSON: {"calendar": [{"week": 1, "channel": "string", "actions": ["string"]}]}"""
    payload = {"kb_context": kb_context[:12000], "ideas": ideas}
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    return parsed or {"calendar": []}


def run_router(
    user_message: str,
    kb_context: str,
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "main_marketing_agent", "routing", "Choosing specialist agents for this turn")
    system = """You route marketing work. Output JSON only:
{"agents": ["marketing_strategist","idea_generator","copywriter","scriptwriter","brand_voice_keeper","competitor_intel","channel_planner","image_generator","video_generator"],
 "rationale": "string"}
Pick a subset (1-6) that fits the user_message. Use image_generator only if user asks for images/visuals/banners. Use video_generator only for video/ads motion. Always include idea_generator OR copywriter for substantive marketing asks."""
    payload = {"user_message": user_message[:4000], "kb_excerpt": kb_context[:6000]}
    parsed, _ = invoke_json(system, payload, task_tier="cheap")
    agents = (parsed or {}).get("agents") or ["idea_generator", "copywriter"]
    if not isinstance(agents, list):
        agents = ["idea_generator", "copywriter"]
    return {"agents": [str(a) for a in agents[:8]], "rationale": str((parsed or {}).get("rationale") or "")}


def run_critic(
    user_message: str,
    kb_context: str,
    draft: str,
    *,
    progress: Callable[..., None] | None = None,
) -> dict[str, Any]:
    _emit(progress, "critic", "review", "Reviewing draft vs ICP and positioning")
    system = """Output JSON: {"approved": true|false, "feedback": "string", "must_fix": ["string"]}"""
    payload = {"user_message": user_message[:4000], "kb_context": kb_context[:8000], "draft": draft[:24000]}
    parsed, _ = invoke_json(system, payload, task_tier="standard")
    approved = bool((parsed or {}).get("approved", True))
    return {
        "approved": approved,
        "feedback": str((parsed or {}).get("feedback") or ""),
        "must_fix": (parsed or {}).get("must_fix") or [],
    }


def run_finalize_reply(
    user_message: str,
    kb_context: str,
    agent_outputs: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> str:
    _emit(progress, "main_marketing_agent", "finalize", "Composing final assistant reply")
    system = """You are the main marketing agent speaking to a startup founder. Write a clear, actionable Markdown reply that weaves in outputs from specialists. Be concise; use headings and bullets."""
    payload = {
        "user_message": user_message[:4000],
        "kb_context": kb_context[:6000],
        "agent_outputs": {k: (v if isinstance(v, (dict, list, str)) else str(v)) for k, v in agent_outputs.items()},
    }
    parsed, _ = invoke_json(
        system + ' Return JSON {"reply_markdown": "string"} only.',
        payload,
        task_tier="premium",
    )
    if isinstance(parsed, dict) and parsed.get("reply_markdown"):
        return str(parsed["reply_markdown"])
    return "## Marketing update\n\nHere is a synthesized response based on your request and our specialist outputs.\n\n```json\n" + json.dumps(agent_outputs, indent=2)[:8000] + "\n```"


def run_memory_curator(
    company_id: str,
    chat_id: str,
    user_message: str,
    final_reply: str,
    agent_outputs: dict[str, Any],
    *,
    progress: Callable[..., None] | None = None,
) -> None:
    _emit(progress, "memory_curator", "memory", "Saving learnings to company knowledge base")
    try:
        from shared_memory.kb import kb_insert

        summary = (final_reply or "")[:4000]
        kb_insert(
            company_id,
            "learning",
            "Marketing chat takeaway",
            f"User ask: {user_message[:2000]}\n\nAssistant summary:\n{summary}",
            tags=["marketing", "chat"],
            source_system="marketing",
            source_chat_id=chat_id,
        )
        ideas = agent_outputs.get("idea_generator") or {}
        if ideas.get("ideas"):
            kb_insert(
                company_id,
                "other",
                "Campaign ideas (from chat)",
                json.dumps(ideas.get("ideas"), indent=2)[:12000],
                tags=["marketing", "ideas"],
                source_system="marketing",
                source_chat_id=chat_id,
            )
    except Exception:
        pass
