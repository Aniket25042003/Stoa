from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_conversation_org, verify_org_exists
from stoa_core.security.pii import redact_pii
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.insights.common import build_executive_summary, precompute_answers
from stoa_core.intelligence.icp import build_icp_profile
from stoa_core.intelligence.structured import aggregate_crm_stats
from stoa_core.rag.answer import answer_question
from stoa_core.rag.ingest import ingest_knowledge, json_artifact_to_text
from stoa_core.rag.retrieve import retrieve_context
from stoa_core.redis.client import publish_event

logger = logging.getLogger(__name__)

INTELLIGENCE_KINDS = [
    "document",
    "company_profile",
    "icp_profile",
    "crm_account",
    "crm_contact",
    "crm_deal",
    "call_transcript",
    "support_ticket",
    "review",
    "product_analytics_summary",
]


def _doc_count(org_id: str) -> int:
    sb = get_supabase_admin()
    res = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    return res.count or 0


def _should_skip_precompute(org_id: str, doc_count: int) -> bool:
    if doc_count == 0:
        return True
    sb = get_supabase_admin()
    existing = (
        sb.table("precomputed_insights")
        .select("source_document_count")
        .eq("org_id", org_id)
        .eq("scope", "intelligence")
        .limit(1)
        .execute()
    )
    if not existing.data:
        return False
    last_count = existing.data[0].get("source_document_count") or 0
    return last_count == doc_count


def _upsert_insight(
    org_id: str,
    *,
    scope: str,
    key: str,
    title: str,
    content: dict,
    citations: list,
    source_document_count: int,
) -> None:
    sb = get_supabase_admin()
    sb.table("precomputed_insights").upsert(
        {
            "org_id": org_id,
            "scope": scope,
            "key": key,
            "title": title,
            "content": content,
            "citations": citations,
            "is_stale": False,
            "source_document_count": source_document_count,
        },
        on_conflict="org_id,scope,key",
    ).execute()


@celery_app.task(name="intelligence.precompute_insights", bind=True, max_retries=2)
def precompute_insights(self, org_id: str, *, force: bool = False) -> None:
    sb = get_supabase_admin()
    try:
        verify_org_exists(org_id)
        doc_count = _doc_count(org_id)
        if not force and _should_skip_precompute(org_id, doc_count):
            logger.info("Skipping precompute for org %s — no new documents", org_id)
            return

        org_res = sb.table("organizations").select("name").eq("id", org_id).limit(1).execute()
        org_name = (org_res.data or [{}])[0].get("name") or "your company"

        for item in precompute_answers(org_id):
            _upsert_insight(
                org_id,
                scope="intelligence",
                key=item["key"],
                title=item["title"],
                content=item["content"],
                citations=item["citations"],
                source_document_count=doc_count,
            )

        exec_summary = build_executive_summary(org_id, org_name)
        if exec_summary.get("summary") is None:
            logger.error("Skipping executive summary upsert for org %s: generation failed", org_id)
            publish_event("insights", org_id, {"status": "partial", "document_count": doc_count})
            return
        _upsert_insight(
            org_id,
            scope="dashboard",
            key="executive_summary",
            title="Executive summary",
            content=exec_summary,
            citations=exec_summary.get("citations", []),
            source_document_count=doc_count,
        )
        publish_event("insights", org_id, {"status": "completed", "document_count": doc_count})
    except Exception as exc:
        logger.exception("Precompute insights failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="intelligence.rebuild_icp", bind=True, max_retries=2)
def rebuild_icp_profile(self, org_id: str) -> None:
    sb = get_supabase_admin()
    try:
        verify_org_exists(org_id)
        signals_res = (
            sb.table("intelligence").select("*").eq("org_id", org_id).order("created_at", desc=True).limit(500).execute()
        )
        signals = signals_res.data or []
        structured = aggregate_crm_stats(org_id)
        has_data = bool(signals) or structured.get("total_deals", 0) > 0 or structured.get("total_accounts", 0) > 0
        profile_data = build_icp_profile(signals, structured_stats=structured if has_data else None)
        if not profile_data:
            return
        version_res = (
            sb.table("icp_profiles").select("version").eq("org_id", org_id).order("version", desc=True).limit(1).execute()
        )
        next_version = ((version_res.data or [{}])[0].get("version") or 0) + 1
        sb.table("icp_profiles").insert(
            {"org_id": org_id, "version": next_version, "profile": profile_data, "signal_count": len(signals)}
        ).execute()

        ingest_knowledge(
            org_id,
            kind="icp_profile",
            title=f"ICP profile v{next_version}",
            text=json_artifact_to_text(profile_data),
            feature_origin="intelligence",
            uri=f"icp_profile:{org_id}:v{next_version}",
            metadata={"version": next_version, "signal_count": len(signals)},
        )

        publish_event("icp", org_id, {"status": "completed", "version": next_version})
        precompute_insights.delay(org_id)
    except Exception as exc:
        logger.exception("ICP rebuild failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="intelligence.answer_question", bind=True, max_retries=2)
def answer_intelligence_question(self, conversation_id: str, org_id: str, question: str) -> None:
    sb = get_supabase_admin()
    try:
        verify_conversation_org(conversation_id, org_id)
        publish_event("conversation", conversation_id, {"status": "thinking", "message": "Retrieving intelligence..."})

        context = retrieve_context(org_id, question, kinds=INTELLIGENCE_KINDS)
        safe_question = redact_pii(question)
        answer = redact_pii(answer_question(safe_question, context))
        sb.table("messages").insert(
            {
                "conversation_id": conversation_id,
                "org_id": org_id,
                "role": "assistant",
                "content": answer,
                "citations": [item["ref"] for item in context[:10]],
            }
        ).execute()
        publish_event("conversation", conversation_id, {"status": "completed", "answer": answer})
    except Exception as exc:
        logger.exception("Answer failed for conversation %s", conversation_id)
        publish_event("conversation", conversation_id, {"status": "failed", "error": "Answer generation failed"})
        raise self.retry(exc=exc, countdown=30) from exc
