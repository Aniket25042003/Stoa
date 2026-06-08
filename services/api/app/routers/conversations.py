from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import sanitize_user_content

from app.services.org_context import get_user_membership, require_role
from app.tasks.intelligence import answer_intelligence_question
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.redis.sse import read_events_since

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@router.get("")
def list_conversations(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("conversations")
        .select("id, org_id, title, created_by, created_at, updated_at")
        .eq("org_id", membership["org_id"])
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"conversations": res.data or []}


@router.post("/ask")
def ask_question(body: AskBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "viewer")
    check_rate_limit(user_id, get_settings().rate_limit_per_minute, scope="ask")
    question = redact_pii(sanitize_user_content(body.question))
    sb = get_supabase_admin()
    conv_id = str(uuid.uuid4())
    sb.table("conversations").insert(
        {"id": conv_id, "org_id": membership["org_id"], "title": question[:120], "created_by": user_id}
    ).execute()
    msg_res = (
        sb.table("messages")
        .insert({"conversation_id": conv_id, "role": "user", "content": question, "org_id": membership["org_id"]})
        .execute()
    )
    user_msg = (msg_res.data or [None])[0]
    answer_intelligence_question.delay(conv_id, membership["org_id"], question)
    write_audit(membership["org_id"], user_id, "conversation.asked", "conversation", conv_id)
    return {"conversation_id": conv_id, "message": user_msg, "status": "processing"}


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    conv = (
        sb.table("conversations")
        .select("id, org_id, title, created_by, created_at, updated_at")
        .eq("id", conversation_id)
        .eq("org_id", membership["org_id"])
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


@router.get("/{conversation_id}/events")
async def conversation_events(
    conversation_id: str,
    last_id: str | None = None,
    user_id: str = Depends(verify_supabase_jwt),
) -> StreamingResponse:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    conv = (
        sb.table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("org_id", membership["org_id"])
        .limit(1)
        .execute()
    )
    if not conv.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    async def gen():
        async for msg_id, data in read_events_since("conversation", conversation_id, last_id):
            payload = json.dumps({"id": msg_id, **data})
            yield f"data: {payload}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
