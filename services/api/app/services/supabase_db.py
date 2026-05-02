from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client

from app.config import get_settings


def get_supabase_admin() -> Client:
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        raise RuntimeError("Supabase admin client not configured")
    return create_client(s.supabase_url, s.supabase_service_role_key)


def insert_run(user_id: str, input_payload: dict[str, Any], master_plan: dict[str, Any] | None = None) -> str:
    sb = get_supabase_admin()
    row = (
        sb.table("gtm_runs")
        .insert(
            {
                "user_id": user_id,
                "status": "awaiting_plan_approval",
                "run_input": input_payload,
                "master_plan": master_plan or {},
            }
        )
        .execute()
    )
    data = row.data
    if not data:
        raise RuntimeError("Failed to insert gtm_run")
    return str(data[0]["id"])


def update_master_plan(run_id: str, master_plan: dict[str, Any], feedback: str | None = None) -> None:
    sb = get_supabase_admin()
    payload: dict[str, Any] = {"master_plan": master_plan, "status": "awaiting_plan_approval"}
    if feedback is not None:
        payload["plan_feedback"] = feedback
    sb.table("gtm_runs").update(payload).eq("id", run_id).execute()


def approve_master_plan(run_id: str) -> None:
    sb = get_supabase_admin()
    sb.table("gtm_runs").update({"status": "queued", "plan_approved_at": datetime.now(timezone.utc).isoformat()}).eq("id", run_id).execute()


def update_run_status(run_id: str, status: str, error: str | None = None) -> None:
    sb = get_supabase_admin()
    payload: dict[str, Any] = {"status": status}
    if error is not None:
        payload["error"] = error
    sb.table("gtm_runs").update(payload).eq("id", run_id).execute()


def get_run(run_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = sb.table("gtm_runs").select("*").eq("id", run_id).limit(1).execute()
    if res.data:
        return res.data[0]
    return None


def insert_run_event(run_id: str, event_type: str, payload: dict[str, Any]) -> None:
    sb = get_supabase_admin()
    sb.table("run_events").insert({"run_id": run_id, "event_type": event_type, "payload": payload}).execute()


def insert_agent_task(
    run_id: str,
    agent_name: str,
    status: str,
    payload: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("agent_tasks")
        .insert(
            {
                "run_id": run_id,
                "agent_name": agent_name,
                "status": status,
                "payload": payload or {},
                "result": result,
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert agent task")
    return str(res.data[0]["id"])


def insert_agent_artifact(run_id: str, artifact_type: str, content: dict[str, Any], version: int = 1) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("agent_artifacts")
        .insert({"run_id": run_id, "artifact_type": artifact_type, "content": content, "version": version})
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert agent artifact")
    return str(res.data[0]["id"])


def insert_research_sources(run_id: str, items: list[dict[str, Any]]) -> None:
    if not items:
        return
    sb = get_supabase_admin()
    rows = []
    for it in items:
        rows.append(
            {
                "run_id": run_id,
                "source_type": it.get("source_type", "other"),
                "source_url": it.get("source_url"),
                "title": it.get("title"),
                "excerpt": it.get("raw_excerpt") or it.get("summary"),
                "retrieved_at": it.get("retrieved_at"),
                "metadata": {
                    "query": it.get("query"),
                    "summary": it.get("summary"),
                    "sentiment": it.get("sentiment"),
                    "confidence": it.get("confidence"),
                    **(it.get("metadata") or {}),
                },
            }
        )
    sb.table("research_sources").insert(rows).execute()


def list_research_sources(run_id: str, limit: int = 200) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("research_sources")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def insert_report(run_id: str, markdown: str) -> str:
    sb = get_supabase_admin()
    res = sb.table("gtm_reports").insert({"run_id": run_id, "markdown": markdown, "version": 1}).execute()
    if not res.data:
        raise RuntimeError("Failed to insert report")
    return str(res.data[0]["id"])


def get_latest_report(run_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("gtm_reports")
        .select("*")
        .eq("run_id", run_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None


def list_run_events(run_id: str, limit: int = 500) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("run_events")
        .select("id,payload,created_at")
        .eq("run_id", run_id)
        .order("id", desc=False)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def list_runs_for_user(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("gtm_runs")
        .select("id,status,created_at,updated_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])
