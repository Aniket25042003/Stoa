from __future__ import annotations

import os
from typing import Any

from app.celery_app import celery_app
from app.services import supabase_db
from app.services.redis_sync import publish_event_sync


def _emit(run_id: str, agent: str, phase: str, message: str, detail: dict[str, Any] | None = None) -> None:
    payload = {
        "run_id": run_id,
        "level": "info",
        "agent": agent,
        "phase": phase,
        "message": message,
        "detail": detail or {},
    }
    publish_event_sync(run_id, payload)
    try:
        supabase_db.insert_run_event(run_id, "progress", payload)
    except Exception:
        return


def _record_task(run_id: str, agent: str, status: str, payload: dict[str, Any] | None = None, result: dict[str, Any] | None = None) -> None:
    try:
        supabase_db.insert_agent_task(run_id, agent, status, payload=payload, result=result)
    except Exception as e:
        _emit(run_id, agent, "system", f"Task persistence warning: {e}")


def _record_artifact(run_id: str, artifact_type: str, content: dict[str, Any]) -> None:
    try:
        supabase_db.insert_agent_artifact(run_id, artifact_type, content)
    except Exception as e:
        _emit(run_id, "artifact_store", "system", f"Artifact persistence warning: {e}")


@celery_app.task(name="gtm.run_pipeline")
def run_pipeline_task(run_id: str, user_id: str) -> dict[str, Any]:
    if os.getenv("LANGCHAIN_TRACING_V2") == "true" and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

    from gtm_agents.graph import build_graph
    from gtm_agents.memory import read_memory

    _emit(run_id, "celery", "research", "Starting GTM pipeline")
    supabase_db.update_run_status(run_id, "running")

    try:
        run_row = supabase_db.get_run(run_id)
        inp = (run_row or {}).get("run_input") or {}

        initial: dict[str, Any] = {
            "run_id": run_id,
            "user_id": user_id,
            "input": inp,
        }
        _emit(run_id, "orchestrator", "research", "Planning research objectives")
        _record_task(run_id, "orchestrator", "running", payload=inp)
        app = build_graph()
        result = app.invoke(initial)
        _record_task(
            run_id,
            "orchestrator",
            "completed",
            result={"master_plan": result.get("master_plan"), "approvals": result.get("approvals")},
        )
        _record_artifact(run_id, "master_plan", result.get("master_plan") or {})
        _record_artifact(run_id, "agent_plans", result.get("agent_plans") or {})
        _record_artifact(run_id, "approvals", result.get("approvals") or {})
        _record_artifact(run_id, "redis_memory_tail", {"memory": read_memory(run_id, 100)})
        _record_artifact(run_id, "research_plan", result.get("research_plan") or {})

        items = result.get("research_items") or []
        tool_errors = result.get("tool_errors") or []
        _record_task(
            run_id,
            "research_supervisor",
            "completed",
            result={"source_count": len(items), "warnings": tool_errors},
        )
        _emit(run_id, "research_supervisor", "research", f"Collected {len(items)} research source(s)", {"warnings": tool_errors})
        try:
            supabase_db.insert_research_sources(run_id, list(items))
        except Exception as e:
            _emit(run_id, "research_supervisor", "research", f"Source persistence warning: {e}")
        _record_artifact(
            run_id,
            "research_bundle",
            {
                "research_bundle": result.get("research_bundle") or {},
                "tool_results": result.get("tool_results") or [],
                "warnings": tool_errors,
            },
        )

        for artifact_type, agent_name, message in (
            ("segmentation", "segmentation", "ICP / personas drafted"),
            ("positioning", "positioning", "Messaging angles drafted"),
            ("channels", "channels", "Channel ranking drafted"),
            ("validation", "validator", "Citation and source validation completed"),
        ):
            content = result.get(artifact_type) or {}
            _record_task(run_id, agent_name, "completed", result=content)
            _record_artifact(run_id, artifact_type, content)
            _emit(run_id, agent_name, "reasoning", message, content if artifact_type == "validation" else {})

        md = str(result.get("final_markdown") or "")
        supabase_db.insert_report(run_id, md)
        _record_task(run_id, "writer", "completed", result={"markdown_chars": len(md)})
        _record_artifact(run_id, "final_report_markdown", {"markdown": md})
        _emit(run_id, "writer", "writing", "GTM Markdown report saved")

        supabase_db.update_run_status(run_id, "completed")
        _emit(run_id, "orchestrator", "writing", "Pipeline completed")
        return {"ok": True, "run_id": run_id}
    except Exception as e:
        supabase_db.update_run_status(run_id, "failed", error=str(e))
        _emit(run_id, "orchestrator", "writing", f"Failed: {e}", {"error": str(e)})
        raise
