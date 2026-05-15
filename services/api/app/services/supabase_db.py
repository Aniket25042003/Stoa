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


def insert_run(
    user_id: str,
    input_payload: dict[str, Any],
    master_plan: dict[str, Any] | None = None,
    status: str = "awaiting_plan_approval",
    company_id: str | None = None,
) -> str:
    sb = get_supabase_admin()
    insert_body: dict[str, Any] = {
        "user_id": user_id,
        "status": status,
        "run_input": input_payload,
        "master_plan": master_plan or {},
    }
    if company_id:
        insert_body["company_id"] = company_id
    row = sb.table("gtm_runs").insert(insert_body).execute()
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
        .select("id,status,created_at,updated_at,company_id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


# --- Companies & marketing (shared KB workspace) ---


COMPANY_PROFILE_FIELDS = (
    "description",
    "brand_voice",
    "website_url",
    "industry",
    "target_customers",
    "geography",
    "business_model",
    "stage",
    "goals",
    "known_competitors",
    "constraints",
    "onboarding_completed_at",
)


def insert_company(
    user_id: str,
    name: str,
    description: str | None = None,
    brand_voice: dict[str, Any] | None = None,
    **profile: Any,
) -> str:
    sb = get_supabase_admin()
    body: dict[str, Any] = {
        "user_id": user_id,
        "name": name,
        "description": description,
        "brand_voice": brand_voice or {},
    }
    for key in COMPANY_PROFILE_FIELDS:
        if key in profile and profile[key] is not None:
            body[key] = profile[key]
    res = (
        sb.table("companies")
        .insert(body)
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert company")
    return str(res.data[0]["id"])


def get_company(company_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    r = sb.table("companies").select("*").eq("id", company_id).limit(1).execute()
    return r.data[0] if r.data else None


def list_companies_for_user(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = sb.table("companies").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return list(res.data or [])


def update_company_profile(company_id: str, **profile: Any) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    body: dict[str, Any] = {}
    if "name" in profile and profile["name"] is not None:
        body["name"] = profile["name"]
    for key in COMPANY_PROFILE_FIELDS:
        if key in profile and profile[key] is not None:
            body[key] = profile[key]
    if not body:
        return get_company(company_id)
    res = sb.table("companies").update(body).eq("id", company_id).execute()
    return res.data[0] if res.data else get_company(company_id)


def list_knowledge_for_company(company_id: str, kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    q = sb.table("company_knowledge").select("id,kind,title,content,tags,created_at,updated_at").eq("company_id", company_id)
    if kind:
        q = q.eq("kind", kind)
    res = q.order("updated_at", desc=True).limit(limit).execute()
    return list(res.data or [])


def search_knowledge_text(company_id: str, query: str, kinds: list[str] | None = None, limit: int = 20) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    try:
        res = sb.rpc(
            "kb_search_company_knowledge_text",
            {
                "p_company_id": company_id,
                "p_query": query,
                "p_match_count": limit,
                "p_kinds": kinds,
            },
        ).execute()
        return list(res.data or [])
    except Exception:
        return []


def insert_company_knowledge(
    company_id: str,
    *,
    kind: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    source_system: str | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("company_knowledge")
        .insert(
            {
                "company_id": company_id,
                "kind": kind,
                "title": title,
                "content": content,
                "tags": tags or [],
                "source_system": source_system,
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert company knowledge")
    return str(res.data[0]["id"])


def get_active_gtm_plan(company_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("company_gtm_plans")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_active", True)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def upsert_company_gtm_plan(
    company_id: str,
    *,
    source: str,
    title: str,
    content_markdown: str,
    content_json: dict[str, Any] | None = None,
    source_run_id: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase_admin()
    # Keep a single active plan per company while retaining older rows for history.
    sb.table("company_gtm_plans").update({"is_active": False}).eq("company_id", company_id).eq("is_active", True).execute()
    res = (
        sb.table("company_gtm_plans")
        .insert(
            {
                "company_id": company_id,
                "source": source,
                "title": title,
                "content_markdown": content_markdown,
                "content_json": content_json or {},
                "source_run_id": source_run_id,
                "is_active": True,
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to upsert GTM plan")
    return res.data[0]


def update_company_gtm_plan(
    plan_id: str,
    *,
    content_markdown: str,
    content_json: dict[str, Any] | None = None,
    title: str | None = None,
) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    body: dict[str, Any] = {
        "content_markdown": content_markdown,
        "content_json": content_json or {},
    }
    if title:
        body["title"] = title
    res = sb.table("company_gtm_plans").update(body).eq("id", plan_id).execute()
    return res.data[0] if res.data else None


def insert_gtm_plan_message(
    company_id: str,
    role: str,
    content: str,
    *,
    plan_id: str | None = None,
    parts: dict[str, Any] | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("gtm_plan_messages")
        .insert(
            {
                "company_id": company_id,
                "plan_id": plan_id,
                "role": role,
                "content": content,
                "parts": parts or {},
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert GTM plan message")
    return str(res.data[0]["id"])


def list_gtm_plan_messages(company_id: str, limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("gtm_plan_messages")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def list_company_marketing_artifacts(company_id: str, limit: int = 20) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_artifacts")
        .select("*, marketing_chats!inner(company_id)")
        .eq("marketing_chats.company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def insert_marketing_chat(user_id: str, company_id: str, title: str | None = None) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_chats")
        .insert(
            {
                "user_id": user_id,
                "company_id": company_id,
                "title": title or "Marketing chat",
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert marketing chat")
    return str(res.data[0]["id"])


def list_marketing_chats(company_id: str, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_chats")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def get_marketing_chat(chat_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    r = sb.table("marketing_chats").select("*").eq("id", chat_id).limit(1).execute()
    return r.data[0] if r.data else None


def insert_marketing_message(
    chat_id: str,
    role: str,
    content: str,
    *,
    agent: str | None = None,
    parts: dict[str, Any] | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_messages")
        .insert(
            {
                "chat_id": chat_id,
                "role": role,
                "agent": agent,
                "content": content,
                "parts": parts or {},
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert marketing message")
    return str(res.data[0]["id"])


def list_marketing_messages(chat_id: str, limit: int = 200) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def insert_marketing_task(
    chat_id: str,
    agent_name: str,
    status: str,
    *,
    message_id: str | None = None,
    payload: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_tasks")
        .insert(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "agent_name": agent_name,
                "status": status,
                "payload": payload or {},
                "result": result,
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert marketing task")
    return str(res.data[0]["id"])


def update_marketing_task(task_id: str, status: str, result: dict[str, Any] | None = None) -> None:
    sb = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()
    body: dict[str, Any] = {"status": status}
    if result is not None:
        body["result"] = result
    if status == "running":
        body["started_at"] = now
    if status in ("completed", "failed"):
        body["finished_at"] = now
    sb.table("marketing_tasks").update(body).eq("id", task_id).execute()


def insert_marketing_artifact(
    chat_id: str,
    kind: str,
    title: str,
    *,
    task_id: str | None = None,
    storage_path: str | None = None,
    mime_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_artifacts")
        .insert(
            {
                "chat_id": chat_id,
                "task_id": task_id,
                "kind": kind,
                "title": title,
                "storage_path": storage_path,
                "mime_type": mime_type,
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    if not res.data:
        raise RuntimeError("Failed to insert marketing artifact")
    return str(res.data[0]["id"])


def list_marketing_artifacts(chat_id: str, limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("marketing_artifacts")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def get_marketing_artifact(artifact_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    r = sb.table("marketing_artifacts").select("*").eq("id", artifact_id).limit(1).execute()
    return r.data[0] if r.data else None


def list_gtm_runs_for_company(company_id: str, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("gtm_runs")
        .select("id,status,created_at,updated_at")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])
