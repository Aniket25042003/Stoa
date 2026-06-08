from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.services import supabase_db
from app.services.supabase_db import get_supabase_admin
from app.services.redis_events import read_marketing_events_since
from app.tasks.marketing import run_chat_turn_task

logger = logging.getLogger(__name__)

router = APIRouter(tags=["marketing"])


class CreateChatBody(BaseModel):
    title: str | None = Field(None, max_length=200)


class PostMessageBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)


@router.post("/v1/companies/{company_id}/chats")
def create_chat(
    company_id: str,
    body: CreateChatBody,
    user_id: str = Depends(verify_supabase_jwt),
) -> dict[str, Any]:
    co = supabase_db.get_company(company_id)
    if not co or co.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    cid = supabase_db.insert_marketing_chat(user_id, company_id, body.title)
    return {"id": cid}


@router.get("/v1/companies/{company_id}/chats")
def list_chats(company_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    co = supabase_db.get_company(company_id)
    if not co or co.get("user_id") != user_id:
        raise HTTPException(404, "Company not found")
    return {"chats": supabase_db.list_marketing_chats(company_id)}


@router.get("/v1/chats/{chat_id}")
def get_chat(chat_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    ch = supabase_db.get_marketing_chat(chat_id)
    if not ch or ch.get("user_id") != user_id:
        raise HTTPException(404, "Chat not found")
    co = supabase_db.get_company(str(ch.get("company_id")))
    if not co or co.get("user_id") != user_id:
        raise HTTPException(404, "Chat not found")
    return {
        "chat": ch,
        "messages": supabase_db.list_marketing_messages(chat_id),
        "artifacts": supabase_db.list_marketing_artifacts(chat_id),
    }


@router.post("/v1/chats/{chat_id}/messages")
def post_message(chat_id: str, body: PostMessageBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    ch = supabase_db.get_marketing_chat(chat_id)
    if not ch or ch.get("user_id") != user_id:
        raise HTTPException(404, "Chat not found")
    mid = supabase_db.insert_marketing_message(chat_id, "user", body.content)
    run_chat_turn_task.delay(chat_id, user_id, mid)
    return {"message_id": mid, "status": "queued"}


async def _sse_gen(chat_id: str, user_id: str) -> AsyncGenerator[bytes, None]:
    ch = supabase_db.get_marketing_chat(chat_id)
    if not ch or ch.get("user_id") != user_id:
        yield f"event: error\ndata: {json.dumps({'message': 'not found'})}\n\n".encode()
        return

    try:
        async for msg_id, data in read_marketing_events_since(chat_id, "$"):
            if msg_id == "heartbeat":
                yield b": heartbeat\n\n"
                continue
            try:
                payload = json.dumps(data, default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                payload = json.dumps({"message": "event", "detail": "non-serializable payload omitted"}, default=str)
            yield f"event: progress\ndata: {payload}\n\n".encode()
            if data.get("message") == "Pipeline completed":
                return
            if data.get("phase") == "error" and data.get("detail", {}).get("error"):
                return
    except asyncio.CancelledError:
        raise
    except Exception:
        yield f"event: error\ndata: {json.dumps({'message': 'stream interrupted'})}\n\n".encode()


@router.get("/v1/chats/{chat_id}/events")
async def stream_chat_events(chat_id: str, user_id: str = Depends(verify_supabase_jwt)) -> StreamingResponse:
    return StreamingResponse(
        _sse_gen(chat_id, user_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/v1/artifacts/{artifact_id}/signed-url")
def artifact_signed_url(artifact_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    art = supabase_db.get_marketing_artifact(artifact_id)
    if not art or not art.get("storage_path"):
        raise HTTPException(404, "Artifact not found")
    ch = supabase_db.get_marketing_chat(str(art.get("chat_id")))
    if not ch or ch.get("user_id") != user_id:
        raise HTTPException(404, "Artifact not found")
    import os

    bucket = (os.getenv("MKT_STORAGE_BUCKET") or "marketing-assets").strip()
    sb = get_supabase_admin()
    try:
        signed = sb.storage.from_(bucket).create_signed_url(str(art["storage_path"]), 3600)
        url = signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url")
        if not url:
            raise HTTPException(503, "Could not sign URL")
        return {"url": url, "mime_type": art.get("mime_type"), "title": art.get("title")}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("artifact_signed_url failed: %s", exc)
        raise HTTPException(503, "Could not create download link") from exc
