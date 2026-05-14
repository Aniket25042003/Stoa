"""Typed state for one marketing chat turn (LangGraph)."""

from __future__ import annotations

from typing import Any, Callable, NotRequired, TypedDict


class MarketingTurnState(TypedDict, total=False):
    chat_id: str
    company_id: str
    user_id: str
    user_message: str
    message_id: str
    history: list[dict[str, Any]]
    kb_context: str
    routed_agents: list[str]
    routing_rationale: str
    agent_outputs: dict[str, Any]
    draft: str
    critic_ok: bool
    critic_feedback: str
    final_reply: str
    artifacts: list[dict[str, Any]]
    progress_callback: Callable[[str, str, str, dict[str, Any] | None], None]
