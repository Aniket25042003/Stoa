"""Conversation long-term memory checkpoints."""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.pipeline import CONVERSATION_MEMORY_KIND
from stoa_core.llm.router import invoke_text
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)

CHECKPOINT_EVERY_USER_TURNS = 6
SHORT_TERM_RECENT_MESSAGES = 28


def _load_messages(conversation_id: str, *, limit: int = 80) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return res.data or []


def _count_user_turns(messages: list[dict[str, Any]]) -> int:
    return sum(1 for m in messages if m.get("role") == "user")


def maybe_checkpoint_conversation(org_id: str, conversation_id: str) -> dict[str, Any]:
    messages = _load_messages(conversation_id)
    user_turns = _count_user_turns(messages)
    if user_turns < CHECKPOINT_EVERY_USER_TURNS or user_turns % CHECKPOINT_EVERY_USER_TURNS != 0:
        return {"checkpointed": False, "user_turns": user_turns}

    older = (
        messages[:-SHORT_TERM_RECENT_MESSAGES]
        if len(messages) > SHORT_TERM_RECENT_MESSAGES
        else messages[:-4]
    )
    if not older:
        return {"checkpointed": False, "user_turns": user_turns}

    transcript = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')[:500]}" for m in older)
    summary, _ = invoke_text(
        "Summarize this conversation thread for long-term agent memory. "
        "Capture decisions, facts learned, and open questions.",
        transcript[:12000],
        task_name="summarize",
    )
    summary = redact_pii((summary or "").strip())
    if not summary:
        return {"checkpointed": False, "user_turns": user_turns}

    item = ingest_knowledge(
        org_id,
        kind=CONVERSATION_MEMORY_KIND,
        title=f"Conversation memory checkpoint (turn {user_turns})",
        text=summary,
        feature_origin="agent",
        uri=f"conversation:{conversation_id}:checkpoint:{user_turns}",
        metadata={"conversation_id": conversation_id, "user_turn_count": user_turns},
    )
    return {
        "checkpointed": True,
        "user_turns": user_turns,
        "knowledge_item_id": (item or {}).get("id"),
    }
