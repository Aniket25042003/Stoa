from __future__ import annotations

import os
from typing import Any

from app.celery_app import celery_app
from app.services import supabase_db
from app.services.redis_marketing import publish_marketing_event_sync

from gtm_agents.observability import (
    flush_traces,
    graph_invoke_config,
    pipeline_tracing_context,
    root_trace,
    sync_langsmith_env_from_legacy,
)


def _emit(chat_id: str, agent: str, phase: str, message: str, detail: dict[str, Any] | None = None) -> None:
    payload = {
        "chat_id": chat_id,
        "level": "info",
        "agent": agent,
        "phase": phase,
        "message": message,
        "detail": detail or {},
    }
    publish_marketing_event_sync(chat_id, payload)


@celery_app.task(name="marketing.run_chat_turn")
def run_chat_turn_task(chat_id: str, user_id: str, message_id: str) -> dict[str, Any]:
    sync_langsmith_env_from_legacy()
    if os.getenv("LANGCHAIN_TRACING_V2") == "true" and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

    from marketing_agents.graph import run_marketing_turn
    from marketing_agents.state import MarketingTurnState

    chat = supabase_db.get_marketing_chat(chat_id)
    if not chat or chat.get("user_id") != user_id:
        raise RuntimeError("Chat not found")
    company_id = str(chat.get("company_id") or "")
    msgs = supabase_db.list_marketing_messages(chat_id, limit=100)
    user_msg = next((m for m in reversed(msgs) if str(m.get("id")) == message_id), None)
    user_text = str((user_msg or {}).get("content") or "")

    _emit(chat_id, "celery", "start", "Marketing agents starting", {"message_id": message_id})

    initial: MarketingTurnState = {
        "chat_id": chat_id,
        "company_id": company_id,
        "user_id": user_id,
        "user_message": user_text,
        "message_id": message_id,
        "history": msgs,
        "progress_callback": lambda agent, phase, message, detail=None: _emit(chat_id, agent, phase, message, detail),
    }

    try:
        with pipeline_tracing_context(chat_id, user_id):
            with root_trace(
                "marketing.run_chat_turn",
                "chain",
                {"chat_id": chat_id, "company_id": company_id, "input_summary": user_text[:500]},
            ):
                from marketing_agents.graph import build_marketing_turn_graph

                app = build_marketing_turn_graph()
                cfg = graph_invoke_config(chat_id, user_id)
                out = app.invoke(initial, config=cfg)

        final = str(out.get("final_reply") or "").strip() or "_(No response generated)_"
        supabase_db.insert_marketing_message(
            chat_id,
            "assistant",
            final,
            agent="main_marketing_agent",
            parts={"agent_outputs": out.get("agent_outputs"), "routing": out.get("routing_rationale")},
        )

        outputs = out.get("agent_outputs") or {}
        img = outputs.get("image_generator") or {}
        if isinstance(img, dict) and img.get("ok") and img.get("storage_path"):
            supabase_db.insert_marketing_artifact(
                chat_id,
                "image",
                "Generated image",
                storage_path=str(img["storage_path"]),
                mime_type=str(img.get("mime_type") or "image/png"),
                metadata=dict(img.get("metadata") or {}),
            )
        vid = outputs.get("video_generator") or {}
        if isinstance(vid, dict) and vid.get("storage_path"):
            supabase_db.insert_marketing_artifact(
                chat_id,
                "video",
                "Generated video (pending or stub)",
                storage_path=str(vid.get("storage_path")),
                mime_type=str(vid.get("mime_type") or "video/mp4"),
                metadata=dict(vid.get("metadata") or {}),
            )

        _emit(chat_id, "main_marketing_agent", "done", "Pipeline completed", {})
        return {"ok": True, "chat_id": chat_id}
    except Exception as e:
        _emit(chat_id, "celery", "error", f"Failed: {e}", {"error": str(e)})
        supabase_db.insert_marketing_message(
            chat_id,
            "assistant",
            f"Sorry, something went wrong: {e}",
            agent="system",
            parts={"error": str(e)},
        )
        raise
    finally:
        flush_traces()
