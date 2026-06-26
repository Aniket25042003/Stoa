"""Company and competitor enrichment pipelines."""

from __future__ import annotations

import logging
import re
from typing import Any

from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import content_hash, ingest_knowledge, profile_to_knowledge_text
from stoa_core.research.distill import (
    distill_company_research,
    distill_competitor_research,
    format_research_bundle,
)
from stoa_core.research.fetch import fetch_page_text
from stoa_core.research.serp import research_competitors
from stoa_core.research.types import ResearchItem
from stoa_core.research.web import research_web
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import sanitize_user_content

logger = logging.getLogger(__name__)

COMPANY_WEB_RESEARCH_KIND = "company_web_research"
COMPETITIVE_RESEARCH_KIND = "competitive_research"
CONVERSATION_MEMORY_KIND = "conversation_memory"
CRM_LANDSCAPE_KIND = "crm_landscape"
REVIEW_THEMES_KIND = "review_themes"


def parse_competitor_names(notes: str, *, max_names: int = 5) -> list[str]:
    if not notes or not notes.strip():
        return []
    parts = re.split(r"[\n,;]+", notes)
    names: list[str] = []
    for part in parts:
        name = part.strip()
        if len(name) < 2:
            continue
        if name.lower() in {"and", "etc", "none"}:
            continue
        names.append(name[:120])
        if len(names) >= max_names:
            break
    return names


def run_company_enrichment(org_id: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.disable_external_research:
        return {"skipped": True, "reason": "external_research_disabled"}

    sb = get_supabase_admin()
    org_res = (
        sb.table("organizations")
        .select("id, name, website_url, industry, profile")
        .eq("id", org_id)
        .limit(1)
        .execute()
    )
    org = (org_res.data or [None])[0]
    if not org:
        raise ValueError(f"Organization not found: {org_id}")

    name = org.get("name") or "Company"
    industry = org.get("industry") or ""
    website = org.get("website_url") or ""
    profile_text = profile_to_knowledge_text(org)

    items: list[ResearchItem] = []
    warnings: list[str] = []

    if website:
        page_text = redact_pii(sanitize_user_content(fetch_page_text(website)))
        if page_text:
            items.append(
                ResearchItem(
                    source_type="fetch",
                    title=f"{name} website",
                    raw_excerpt=page_text[:4000],
                    summary=page_text[:800],
                    source_url=website,
                    confidence=0.85,
                )
            )

    web_query = f"{name} {industry} company".strip()
    web_result = research_web(web_query, product_context=profile_text[:500])
    items.extend(web_result.items)
    warnings.extend(web_result.warnings)

    if industry:
        serp_result = research_competitors(f"{name} {industry} competitors overview")
        items.extend(serp_result.items)
        warnings.extend(serp_result.warnings)

    bundle = redact_pii(sanitize_user_content(format_research_bundle(items)))
    if not bundle.strip():
        return {"ingested": False, "warnings": warnings, "items": 0}

    distilled = distill_company_research(name, profile_text, bundle)

    merged_profile = f"{profile_text}\n\n## Web research summary\n{distilled.get('summary', '')}"
    if distilled.get("products"):
        merged_profile += "\n\nProducts: " + ", ".join(distilled["products"][:12])
    if distilled.get("positioning"):
        merged_profile += f"\n\nPositioning: {distilled['positioning']}"

    ingest_knowledge(
        org_id,
        kind="company_profile",
        title=f"{name} profile",
        text=merged_profile,
        feature_origin="enrichment",
        uri=f"org:{org_id}:company_profile",
        metadata={"source": "enrichment", "org_id": org_id},
        force=True,
    )
    web_item = ingest_knowledge(
        org_id,
        kind=COMPANY_WEB_RESEARCH_KIND,
        title=f"{name} web research",
        text=bundle,
        summary=distilled.get("summary"),
        feature_origin="enrichment",
        uri=f"org:{org_id}:web_research:{content_hash(bundle)}",
        metadata={"warnings": warnings, "item_count": len(items)},
    )

    return {
        "ingested": True,
        "warnings": warnings,
        "items": len(items),
        "knowledge_item_id": (web_item or {}).get("id"),
        "distilled": distilled,
    }


def run_competitor_enrichment(org_id: str, competitor_id: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.disable_external_research:
        return {"skipped": True, "reason": "external_research_disabled"}

    sb = get_supabase_admin()
    comp_res = (
        sb.table("competitors")
        .select("id, org_id, name, website_url, pricing_url")
        .eq("id", competitor_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    competitor = (comp_res.data or [None])[0]
    if not competitor:
        raise ValueError(f"Competitor not found: {competitor_id}")

    org_res = sb.table("organizations").select("name").eq("id", org_id).limit(1).execute()
    org_name = ((org_res.data or [{}])[0]).get("name") or "Our company"

    name = competitor.get("name") or "Competitor"
    items: list[ResearchItem] = []
    warnings: list[str] = []

    for url in (competitor.get("website_url"), competitor.get("pricing_url")):
        if not url:
            continue
        page_text = redact_pii(sanitize_user_content(fetch_page_text(url)))
        if page_text:
            items.append(
                ResearchItem(
                    source_type="fetch",
                    title=f"{name} page",
                    raw_excerpt=page_text[:4000],
                    summary=page_text[:800],
                    source_url=url,
                    confidence=0.85,
                )
            )

    for query in (
        f"{name} vs {org_name}",
        f"{name} pricing features",
    ):
        result = research_web(query, max_results=5)
        items.extend(result.items)
        warnings.extend(result.warnings)

    if not competitor.get("website_url"):
        serp = research_competitors(f"{name} official website")
        items.extend(serp.items)
        warnings.extend(serp.warnings)
        for item in serp.items:
            if item.source_url and not competitor.get("website_url"):
                sb.table("competitors").update({"website_url": item.source_url}).eq(
                    "id", competitor_id
                ).execute()
                competitor["website_url"] = item.source_url
                break

    bundle = redact_pii(sanitize_user_content(format_research_bundle(items)))
    if not bundle.strip():
        return {"ingested": False, "warnings": warnings, "items": 0}

    distilled = distill_competitor_research(name, org_name, bundle)
    snapshot_text = redact_pii(
        sanitize_user_content(
            f"# {name} competitive research\n\n{distilled.get('summary', '')}\n\n"
            f"Positioning: {distilled.get('positioning', '')}\n"
            f"Features: {', '.join(distilled.get('feature_highlights', [])[:10])}\n"
            f"Pricing signals: {', '.join(distilled.get('pricing_signals', [])[:8])}"
        )
    )

    snapshot = ingest_knowledge(
        org_id,
        kind="competitive_snapshot",
        title=f"{name} enrichment snapshot",
        text=snapshot_text,
        feature_origin="enrichment",
        uri=f"competitor:{competitor_id}:enrichment:{content_hash(snapshot_text)}",
        metadata={"competitor_id": competitor_id, "source": "enrichment"},
    )
    research_item = ingest_knowledge(
        org_id,
        kind=COMPETITIVE_RESEARCH_KIND,
        title=f"{name} research bundle",
        text=bundle,
        feature_origin="enrichment",
        uri=f"competitor:{competitor_id}:research:{content_hash(bundle)}",
        metadata={"competitor_id": competitor_id, "warnings": warnings},
    )

    return {
        "ingested": True,
        "warnings": warnings,
        "items": len(items),
        "snapshot_id": (snapshot or {}).get("id"),
        "research_id": (research_item or {}).get("id"),
        "distilled": distilled,
    }


def seed_competitors_from_notes(
    org_id: str, notes: str, *, created_by: str | None = None
) -> list[str]:
    names = parse_competitor_names(notes)
    if not names:
        return []
    sb = get_supabase_admin()
    created_ids: list[str] = []
    for name in names:
        existing = (
            sb.table("competitors")
            .select("id")
            .eq("org_id", org_id)
            .ilike("name", name)
            .limit(1)
            .execute()
        )
        if existing.data:
            created_ids.append(existing.data[0]["id"])
            continue
        import uuid

        comp_id = str(uuid.uuid4())
        sb.table("competitors").insert(
            {
                "id": comp_id,
                "org_id": org_id,
                "name": name,
                "created_by": created_by,
            }
        ).execute()
        created_ids.append(comp_id)
    return created_ids
