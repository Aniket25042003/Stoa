from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_org_exists
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge, json_artifact_to_text, profile_to_knowledge_text
from stoa_core.redis.client import publish_event
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)


@celery_app.task(name="knowledge.reembed_org", bind=True, max_retries=2)
def reembed_org(self, org_id: str) -> None:
    """Backfill documents and derived artifacts into the unified knowledge base."""
    try:
        verify_org_exists(org_id)
    except ValueError as exc:
        logger.warning("Rejected knowledge reembed for org %s: %s", org_id, exc)
        return

    sb = get_supabase_admin()
    try:
        docs_res = (
            sb.table("documents")
            .select("id, title, content, doc_type")
            .eq("org_id", org_id)
            .eq("status", "processed")
            .execute()
        )
        for doc in docs_res.data or []:
            content = redact_pii(doc.get("content") or "")
            if not content:
                continue
            ingest_knowledge(
                org_id,
                kind="document",
                title=doc.get("title") or "Document",
                text=content,
                feature_origin="intelligence",
                uri=f"document:{doc['id']}",
                metadata={"document_id": doc["id"], "doc_type": doc.get("doc_type")},
                force=True,
            )

        org_res = sb.table("organizations").select("id, name, slug, website_url, industry, profile").eq("id", org_id).limit(1).execute()
        org = (org_res.data or [None])[0]
        if org:
            ingest_knowledge(
                org_id,
                kind="company_profile",
                title=f"{org.get('name', 'Company')} profile",
                text=profile_to_knowledge_text(org),
                feature_origin="data",
                uri=f"org_profile:{org_id}",
                force=True,
            )

        icp_res = (
            sb.table("icp_profiles")
            .select("profile, version")
            .eq("org_id", org_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        icp = (icp_res.data or [None])[0]
        if icp and icp.get("profile"):
            ingest_knowledge(
                org_id,
                kind="icp_profile",
                title=f"ICP profile v{icp.get('version', 1)}",
                text=json_artifact_to_text(icp["profile"]),
                feature_origin="intelligence",
                uri=f"icp_profile:{org_id}:v{icp.get('version', 1)}",
                metadata={"version": icp.get("version")},
                force=True,
            )

        comps_res = (
            sb.table("competitors")
            .select("id, name, last_snapshot")
            .eq("org_id", org_id)
            .execute()
        )
        for comp in comps_res.data or []:
            snap = redact_pii(comp.get("last_snapshot") or "")
            if not snap:
                continue
            ingest_knowledge(
                org_id,
                kind="competitive_snapshot",
                title=f"{comp.get('name', 'Competitor')} snapshot",
                text=snap,
                feature_origin="competitive",
                uri=f"competitor:{comp['id']}",
                metadata={"competitor_id": comp["id"]},
                force=True,
            )

        publish_event("knowledge", org_id, {"status": "reembedded"})
    except Exception as exc:
        logger.exception("Knowledge reembed failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=120) from exc
