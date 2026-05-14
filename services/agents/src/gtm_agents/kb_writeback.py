"""Distill GTM run outputs into the shared company knowledge base."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _supabase():
    import os

    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def write_gtm_run_to_company_kb(
    *,
    company_id: str | None,
    run_id: str | None,
    inp: dict[str, Any],
    research_items: list[dict[str, Any]],
    segmentation: dict[str, Any],
    positioning: dict[str, Any],
    channels: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    """Persist distilled facts to ``company_knowledge`` and ``company_competitors``."""
    if not company_id or not run_id:
        return
    from shared_memory.kb import kb_insert

    product = inp.get("product_name") or "Product"

    # ICP / segmentation
    kb_insert(
        company_id,
        "icp",
        f"{product}: ICP & personas",
        json.dumps(segmentation, indent=2)[:50000],
        tags=["gtm", "segmentation"],
        source_system="gtm",
        source_run_id=run_id,
    )

    # Positioning
    kb_insert(
        company_id,
        "positioning",
        f"{product}: Positioning & messaging",
        json.dumps(positioning, indent=2)[:50000],
        tags=["gtm", "positioning"],
        source_system="gtm",
        source_run_id=run_id,
    )

    # Channels
    kb_insert(
        company_id,
        "channel",
        f"{product}: Channel strategy",
        json.dumps(channels, indent=2)[:50000],
        tags=["gtm", "channels"],
        source_system="gtm",
        source_run_id=run_id,
    )

    # Risks / validation
    kb_insert(
        company_id,
        "risk",
        f"{product}: Validation & risks",
        json.dumps(validation, indent=2)[:12000],
        tags=["gtm", "validation"],
        source_system="gtm",
        source_run_id=run_id,
    )

    # Competitors from research + known list
    competitor_lines: list[str] = []
    seen_urls: set[str] = set()
    for item in research_items or []:
        meta = item.get("metadata") or {}
        if str(item.get("source_type", "")).lower() not in ("serp", "web", "crawl", "other"):
            continue
        title = item.get("title") or ""
        url = item.get("source_url") or ""
        excerpt = item.get("raw_excerpt") or item.get("excerpt") or item.get("summary") or meta.get("summary") or ""
        if not title and not url:
            continue
        line = f"- {title} | {url}\n  {str(excerpt)[:500]}"
        competitor_lines.append(line)
        if url:
            seen_urls.add(url)

    known = inp.get("known_competitors") or []
    if isinstance(known, list):
        for name in known:
            if not name:
                continue
            competitor_lines.append(f"- Known competitor: {name}")

    if competitor_lines:
        kb_insert(
            company_id,
            "competitor",
            f"{product}: Competitor landscape (sources)",
            "\n".join(competitor_lines)[:50000],
            tags=["gtm", "competitors", "research"],
            source_system="gtm",
            source_run_id=run_id,
        )

    sb = _supabase()
    if sb is None:
        return

    # Structured competitor rows (best-effort from known_competitors)
    for name in known if isinstance(known, list) else []:
        nm = str(name).strip()
        if not nm:
            continue
        try:
            sb.table("company_competitors").insert(
                {
                    "company_id": company_id,
                    "name": nm,
                    "url": None,
                    "positioning": None,
                    "channels": {},
                    "ad_examples": [],
                }
            ).execute()
        except Exception as exc:
            logger.debug("competitor insert skip %s: %s", nm, exc)

    logger.info("GTM KB writeback completed for company_id=%s run_id=%s", company_id, run_id)
