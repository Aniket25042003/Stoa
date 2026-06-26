"""Idempotency helpers for conversation ask flow."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from stoa_core.redis.client import get_redis_sync

_ASK_IDEMPOTENCY_PREFIX = "stoa:ask:idempotency:"
_ASK_IDEMPOTENCY_TTL = 86400


def _hash_question(question: str) -> str:
    return hashlib.sha256(question.strip().encode()).hexdigest()[:32]


def get_idempotent_ask(org_id: str, user_id: str, idempotency_key: str) -> dict[str, Any] | None:
    r = get_redis_sync()
    key = f"{_ASK_IDEMPOTENCY_PREFIX}{org_id}:{user_id}:{idempotency_key}"
    raw = r.get(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def store_idempotent_ask(
    org_id: str,
    user_id: str,
    idempotency_key: str,
    *,
    question: str,
    conversation_id: str,
    user_message_id: str,
) -> None:
    r = get_redis_sync()
    key = f"{_ASK_IDEMPOTENCY_PREFIX}{org_id}:{user_id}:{idempotency_key}"
    payload = {
        "question_hash": _hash_question(question),
        "conversation_id": conversation_id,
        "user_message_id": user_message_id,
    }
    r.setex(key, _ASK_IDEMPOTENCY_TTL, json.dumps(payload))


def find_existing_assistant_reply(
    sb: Any,
    *,
    conversation_id: str,
    user_message_id: str,
) -> dict[str, Any] | None:
    """Return assistant message if this user message was already answered."""
    user_res = (
        sb.table("messages")
        .select("id, created_at")
        .eq("id", user_message_id)
        .eq("conversation_id", conversation_id)
        .limit(1)
        .execute()
    )
    if not user_res.data:
        return None
    created_at = user_res.data[0].get("created_at")
    if not created_at:
        return None
    assistant_res = (
        sb.table("messages")
        .select("id, content, citations, created_at")
        .eq("conversation_id", conversation_id)
        .eq("role", "assistant")
        .gte("created_at", created_at)
        .order("created_at")
        .limit(1)
        .execute()
    )
    rows = assistant_res.data or []
    return rows[0] if rows else None
