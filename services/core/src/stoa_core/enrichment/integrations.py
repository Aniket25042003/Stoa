"""Post-integration enrichment summaries."""

from __future__ import annotations

import json
import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.pipeline import CRM_LANDSCAPE_KIND, REVIEW_THEMES_KIND
from stoa_core.intelligence.structured import aggregate_crm_stats
from stoa_core.llm.router import invoke_text
from stoa_core.rag.ingest import content_hash, ingest_knowledge
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)


def synthesize_crm_summary(org_id: str) -> dict[str, Any]:
    stats = aggregate_crm_stats(org_id)
    if not stats.get("total_accounts") and not stats.get("total_deals"):
        return {"ingested": False, "reason": "no_crm_data"}

    text, _ = invoke_text(
        "Create a concise CRM landscape summary for marketing intelligence retrieval.",
        {"crm_stats": json.dumps(stats, default=str)[:15000]},
        task_name="summarize",
    )
    text = redact_pii((text or json.dumps(stats, indent=2))[:50000])
    item = ingest_knowledge(
        org_id,
        kind=CRM_LANDSCAPE_KIND,
        title="CRM landscape summary",
        text=text,
        feature_origin="integrations",
        uri=f"org:{org_id}:crm_landscape:{content_hash(text)}",
        metadata={"source": "crm_sync"},
    )
    return {"ingested": True, "knowledge_item_id": (item or {}).get("id")}


def synthesize_review_themes(org_id: str) -> dict[str, Any]:
    sb = get_supabase_admin()
    res = (
        sb.table("knowledge_items")
        .select("title, content, summary")
        .eq("org_id", org_id)
        .eq("kind", "review")
        .eq("status", "active")
        .limit(40)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return {"ingested": False, "reason": "no_reviews"}

    bundle = "\n\n".join(
        f"{r.get('title', '')}\n{r.get('content') or r.get('summary') or ''}" for r in rows
    )[:30000]
    text, _ = invoke_text(
        "Distill recurring themes from product reviews: praise, complaints, feature requests.",
        {"reviews": bundle},
        task_name="summarize",
    )
    text = redact_pii((text or bundle[:8000])[:50000])
    item = ingest_knowledge(
        org_id,
        kind=REVIEW_THEMES_KIND,
        title="Review themes summary",
        text=text,
        feature_origin="integrations",
        uri=f"org:{org_id}:review_themes:{content_hash(text)}",
        metadata={"review_count": len(rows)},
    )
    return {
        "ingested": True,
        "knowledge_item_id": (item or {}).get("id"),
        "review_count": len(rows),
    }
