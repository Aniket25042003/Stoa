"""
File: services/api/app/routers/conversations.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Redis, Pydantic, stoa_core
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.conversation_memory import delete_conversation_memory
from stoa_core.redis.ask_idempotency import get_idempotent_ask, store_idempotent_ask
from stoa_core.redis.sse import read_events_since
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import sanitize_user_content

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.intelligence import answer_intelligence_question
from stoa_core.security.permissions import permissions_include

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


def _require_conversation_delete(scope: OrgScope) -> None:
    if permissions_include(scope.permissions, "conversations:delete"):
        return
    require_permission(scope, "conversations:ask")


class AskBody(BaseModel):
    """Manage AskBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """

    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


@router.get("")
def list_conversations(
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles list conversations logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "conversations:read")
    sb = get_supabase_admin()
    res = (
        sb.table("conversations")
        .select("id, org_id, title, created_by, created_at, updated_at")
        .eq("org_id", scope.org_id)
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"conversations": res.data or []}


@router.post("/ask")
def ask_question(
    body: AskBody,
    scope: OrgScope = Depends(require_onboarded_scope),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Handles ask question logic for the surrounding Stoa workflow.

    Args:
        body (AskBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "conversations:ask")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="ask")
    question = redact_pii(sanitize_user_content(body.question))
    sb = get_supabase_admin()

    if idempotency_key:
        cached = get_idempotent_ask(scope.org_id, scope.user_id, idempotency_key.strip())
        if cached and cached.get("conversation_id"):
            return {
                "conversation_id": cached["conversation_id"],
                "message": {"id": cached.get("user_message_id")},
                "status": "processing",
                "idempotent": True,
            }

    if body.conversation_id:
        existing = (
            sb.table("conversations")
            .select("id")
            .eq("id", body.conversation_id)
            .eq("org_id", scope.org_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
        conv_id = body.conversation_id
    else:
        conv_id = str(uuid.uuid4())
        sb.table("conversations").insert(
            {
                "id": conv_id,
                "org_id": scope.org_id,
                "title": question[:120],
                "created_by": scope.user_id,
            }
        ).execute()
    msg_res = (
        sb.table("messages")
        .insert(
            {
                "conversation_id": conv_id,
                "role": "user",
                "content": question,
                "org_id": scope.org_id,
            }
        )
        .execute()
    )
    user_msg = (msg_res.data or [None])[0]
    user_message_id = (user_msg or {}).get("id") if isinstance(user_msg, dict) else None
    if idempotency_key and user_message_id:
        store_idempotent_ask(
            scope.org_id,
            scope.user_id,
            idempotency_key.strip(),
            question=question,
            conversation_id=conv_id,
            user_message_id=str(user_message_id),
        )
    answer_intelligence_question.delay(
        conv_id, scope.org_id, question, scope.user_id, str(user_message_id) if user_message_id else None
    )
    write_audit(
        scope.org_id, scope.user_id, "conversation.asked", "conversation", conv_id
    )
    return {"conversation_id": conv_id, "message": user_msg, "status": "processing"}


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str, scope: OrgScope = Depends(require_onboarded_scope)
) -> dict[str, Any]:
    """Handles get conversation logic for the surrounding Stoa workflow.

    Args:
        conversation_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "conversations:read")
    sb = get_supabase_admin()
    conv = (
        sb.table("conversations")
        .select("id, org_id, title, created_by, created_at, updated_at")
        .eq("id", conversation_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not conv.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    msgs = (
        sb.table("messages")
        .select("id, conversation_id, org_id, role, content, citations, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return {"conversation": conv.data[0], "messages": msgs.data or []}


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    delete_memory: bool = Query(False, description="Also remove long-term agent memory for this thread"),
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Delete a conversation thread; optionally purge its long-term memory."""
    _require_conversation_delete(scope)
    check_rate_limit(scope.user_id, limit_per_minute=30, scope="conversation_delete")
    sb = get_supabase_admin()
    conv = (
        sb.table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not conv.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    memory_items_deleted = 0
    if delete_memory:
        memory_items_deleted = delete_conversation_memory(scope.org_id, conversation_id)

    sb.table("conversations").delete().eq("id", conversation_id).eq("org_id", scope.org_id).execute()
    write_audit(
        scope.org_id,
        scope.user_id,
        "conversation.deleted",
        "conversation",
        conversation_id,
        metadata={"delete_memory": delete_memory, "memory_items_deleted": memory_items_deleted},
    )
    return {
        "status": "deleted",
        "conversation_id": conversation_id,
        "memory_deleted": delete_memory,
        "memory_items_deleted": memory_items_deleted,
    }


@router.get("/{conversation_id}/events")
async def conversation_events(
    conversation_id: str,
    last_id: str | None = None,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> StreamingResponse:
    """Asynchronously handles conversation events logic for the surrounding Stoa workflow.

    Args:
        conversation_id (str): Input value used by this workflow step.
        last_id (str | None): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        StreamingResponse: Result produced for the caller.
    """
    require_permission(scope, "conversations:read")
    sb = get_supabase_admin()
    conv = (
        sb.table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not conv.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    async def gen():
        """Asynchronously handles gen logic for the surrounding Stoa workflow.

        Returns:
            Any: Result produced for the caller.
        """
        async for msg_id, data in read_events_since(
            "conversation", conversation_id, last_id
        ):
            payload = json.dumps({"id": msg_id, **data})
            yield f"data: {payload}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
