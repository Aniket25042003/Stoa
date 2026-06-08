from __future__ import annotations

import logging
import uuid

from app.celery_app import celery_app
from app.services.task_context import verify_ingestion_job
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.ingestion.chunk import chunk_text
from stoa_core.ingestion.extract import extract_signals
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.redis.client import publish_event
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)


@celery_app.task(name="ingestion.process_job", bind=True, max_retries=3)
def process_ingestion_job(self, job_id: str) -> None:
    sb = get_supabase_admin()
    try:
        job, doc = verify_ingestion_job(job_id)
    except ValueError as exc:
        logger.warning("Rejected ingestion job %s: %s", job_id, exc)
        sb.table("ingestion_jobs").update({"status": "failed", "error": "processing failed"}).eq("id", job_id).execute()
        return

    sb.table("ingestion_jobs").update({"status": "running"}).eq("id", job_id).execute()

    try:
        text = redact_pii(doc.get("content") or "")
        org_id = doc["org_id"]
        doc_id = doc["id"]

        ingest_knowledge(
            org_id,
            kind="document",
            title=doc.get("title") or "Document",
            text=text,
            feature_origin="intelligence",
            uri=f"document:{doc_id}",
            metadata={"document_id": doc_id, "doc_type": doc.get("doc_type")},
        )

        chunks = chunk_text(text)
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            redacted = redact_pii(chunk.content)
            for signal in extract_signals(redacted, doc_id):
                evidence_quote = redact_pii(signal.get("evidence_quote", "") or "")
                sb.table("intelligence").insert(
                    {
                        "org_id": org_id,
                        "document_id": doc_id,
                        "chunk_id": chunk_id,
                        "kind": signal.get("kind"),
                        "content": redact_pii(signal.get("content") or ""),
                        "confidence": signal.get("confidence", 0.5),
                        "evidence": {"quote": evidence_quote},
                    }
                ).execute()

        sb.table("documents").update({"status": "processed"}).eq("id", doc_id).execute()
        sb.table("ingestion_jobs").update({"status": "completed"}).eq("id", job_id).execute()
        publish_event("ingestion", job_id, {"status": "completed", "document_id": doc_id})

        from app.tasks.intelligence import precompute_insights, rebuild_icp_profile

        rebuild_icp_profile.delay(org_id)
        precompute_insights.delay(org_id)
    except Exception as exc:
        logger.exception("Ingestion job %s failed", job_id)
        sb.table("ingestion_jobs").update({"status": "failed", "error": "processing failed"}).eq("id", job_id).execute()
        raise self.retry(exc=exc, countdown=30) from exc
