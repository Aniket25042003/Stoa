"""Conversation-scoped long-term memory stored in the knowledge base."""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.cache import bump_kb_version

logger = logging.getLogger(__name__)

CONVERSATION_MEMORY_KIND = "conversation_memory"


def _matches_conversation(row: dict[str, Any], conversation_id: str) -> bool:
    uri = row.get("uri") or ""
    prefix = f"conversation:{conversation_id}:"
    if uri.startswith(prefix):
        return True
    if uri.startswith("conversation:"):
        return False
    if not uri:
        meta = row.get("metadata") or {}
        return meta.get("conversation_id") == conversation_id
    return False


def delete_conversation_memory(org_id: str, conversation_id: str) -> int:
    """Remove pgvector knowledge items linked to a conversation thread."""
    sb = get_supabase_admin()
    res = (
        sb.table("knowledge_items")
        .select("id, uri, metadata")
        .eq("org_id", org_id)
        .eq("kind", CONVERSATION_MEMORY_KIND)
        .execute()
    )
    item_ids = [
        row["id"]
        for row in (res.data or [])
        if row.get("id") and _matches_conversation(row, conversation_id)
    ]
    for item_id in item_ids:
        sb.table("knowledge_items").delete().eq("id", item_id).eq("org_id", org_id).execute()
    if item_ids:
        bump_kb_version(org_id)
        logger.info(
            "Deleted %s conversation memory item(s) org=%s conversation=%s",
            len(item_ids),
            org_id,
            conversation_id,
        )
    return len(item_ids)
