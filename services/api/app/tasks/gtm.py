from __future__ import annotations

import os
from typing import Any

from app.celery_app import celery_app
from app.services import supabase_db
from app.services.redis_sync import publish_event_sync

from gtm_agents.observability import (
    flush_traces,
    get_current_trace_correlation,
    graph_invoke_config,
    pipeline_tracing_context,
    redact_value,
    root_trace,
    summarize_run_input,
    sync_langsmith_env_from_legacy,
)


@celery_app.task(name="gtm.create_master_plan")
def create_master_plan_task(
    run_id: str,
    user_id: str,
    user_feedback: str | None = None,
    prior_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from gtm_agents.autonomy import create_master_plan_for_user

    _emit(run_id, "main_agent", "planning", "Drafting the master plan for user approval")
    supabase_db.update_run_status(run_id, "planning")
    try:
        run_row = supabase_db.get_run(run_id)
        if not run_row or run_row.get("user_id") != user_id:
            raise RuntimeError("Run not found for master-plan generation")
        plan = create_master_plan_for_user(
            run_row.get("run_input") or {},
            user_feedback=user_feedback,
            prior_plan=prior_plan or run_row.get("master_plan") or {},
            run_id=run_id,
        )
        supabase_db.update_master_plan(run_id, plan, feedback=user_feedback)
        _emit(run_id, "main_agent", "planning", "Master plan ready for approval", {"step_count": len(plan.get("steps") or [])})
        return {"ok": True, "run_id": run_id}
    except Exception as e:
        supabase_db.update_run_status(run_id, "failed", error=str(e))
        _emit(run_id, "main_agent", "planning", f"Failed: {e}", {"error": str(e)})
        raise


def _emit(run_id: str, agent: str, phase: str, message: str, detail: dict[str, Any] | None = None) -> None:
    payload_detail = dict(detail or {})
    corr = get_current_trace_correlation()
    if corr:
        payload_detail = {**payload_detail, **corr}
    payload = {
        "run_id": run_id,
        "level": "info",
        "agent": agent,
        "phase": phase,
        "message": message,
        "detail": payload_detail,
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
    sync_langsmith_env_from_legacy()
    # Legacy: keep LANGCHAIN_* effective for older deployments
    if os.getenv("LANGCHAIN_TRACING_V2") == "true" and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

    from gtm_agents.graph import build_graph
    from gtm_agents.memory import read_memory

    _emit(run_id, "celery", "research", "Starting GTM pipeline")
    supabase_db.update_run_status(run_id, "running")

    try:
        run_row = supabase_db.get_run(run_id)
        inp = (run_row or {}).get("run_input") or {}
        approved_plan = (run_row or {}).get("master_plan") or {}
        inp = {**inp, "approved_master_plan": approved_plan}

        initial: dict[str, Any] = {
            "run_id": run_id,
            "user_id": user_id,
            "input": inp,
            "progress_callback": lambda agent, phase, message, detail=None: _emit(run_id, agent, phase, message, detail),
        }
        _emit(run_id, "orchestrator", "research", "Planning research objectives")
        _record_task(run_id, "orchestrator", "running", payload=inp)

        with pipeline_tracing_context(run_id, user_id):
            with root_trace(
                "gtm.run_pipeline",
                "chain",
                {
                    "run_id": run_id,
                    "user_id": user_id,
                    "input_summary": summarize_run_input(inp),
                },
            ) as root_rt:
                app = build_graph()
                cfg = graph_invoke_config(run_id, user_id)
                result = app.invoke(initial, config=cfg)

                corr = get_current_trace_correlation()
                if corr:
                    _record_artifact(run_id, "langsmith_correlation", corr)
                    _emit(run_id, "celery", "research", "LangSmith correlation captured", corr)

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

                if root_rt is not None:
                    try:
                        root_rt.end(
                            outputs=redact_value(
                                {
                                    "ok": True,
                                    "run_id": run_id,
                                    "source_count": len(items),
                                    "markdown_chars": len(md),
                                    "warnings_count": len(tool_errors),
                                }
                            )
                        )
                    except Exception:
                        pass

        supabase_db.update_run_status(run_id, "completed")
        _emit(run_id, "orchestrator", "writing", "Pipeline completed")
        return {"ok": True, "run_id": run_id}
    except Exception as e:
        supabase_db.update_run_status(run_id, "failed", error=str(e))
        _emit(run_id, "orchestrator", "writing", f"Failed: {e}", {"error": str(e)})
        raise
    finally:
        flush_traces()
