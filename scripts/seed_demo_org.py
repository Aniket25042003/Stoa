#!/usr/bin/env python3
"""Seed the Stoa demo workspace for product videos.

Usage:
  python scripts/seed_demo_org.py
  python scripts/seed_demo_org.py --reuse
  python scripts/seed_demo_org.py --skip-embeddings
  python scripts/seed_demo_org.py --with-llm-extract  # optional live signal extraction
"""

from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPO_ROOT / "demo" / "nexara"
MANIFEST_PATH = DEMO_ROOT / "manifest.yaml"

# Path setup for stoa_core (+ optional api tasks)
sys.path.insert(0, str(REPO_ROOT / "services" / "core" / "src"))
sys.path.insert(0, str(REPO_ROOT / "services" / "api"))


def _demo_embed_texts(texts: list[str], **kwargs: Any) -> list[list[float]]:
    """Deterministic pseudo-embeddings for local demo seed without cloud auth."""
    from stoa_core.config import get_settings

    dim = get_settings().embed_dimensions
    vectors: list[list[float]] = []
    for text in texts:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        vec: list[float] = []
        while len(vec) < dim:
            for i in range(0, len(seed), 4):
                if len(vec) >= dim:
                    break
                chunk = seed[i : i + 4]
                if len(chunk) < 4:
                    chunk = chunk + b"\x00" * (4 - len(chunk))
                val = struct.unpack("!i", chunk)[0]
                vec.append((val % 2000) / 1000.0 - 1.0)
            seed = hashlib.sha256(seed).digest()
        vectors.append(vec[:dim])
    return vectors


def enable_offline_seed_mode() -> None:
    """Avoid Redis dependency during local demo seeding."""
    import importlib
    import sys

    import stoa_core.rag.cache as cache_mod
    import stoa_core.redis.client as redis_mod

    class _NoRedis:
        _counters: dict[str, int] = {}

        def ping(self) -> bool:
            return True

        def incr(self, key: str, amount: int = 1) -> int:
            self._counters[key] = self._counters.get(key, 0) + amount
            return self._counters[key]

        def get(self, key: str) -> None:
            return None

        def setex(self, key: str, ttl: int, value: str) -> bool:
            return True

        def expire(self, key: str, ttl: int) -> bool:
            return True

    stub = _NoRedis()

    def _stub_bump(org_id: str) -> int:
        return stub.incr(cache_mod.kb_version_key(org_id))

    redis_mod.get_redis_sync = lambda: stub  # type: ignore[assignment]
    cache_mod.bump_kb_version = _stub_bump  # type: ignore[assignment]

    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith("stoa_core") and hasattr(mod, "bump_kb_version"):
            mod.bump_kb_version = _stub_bump  # type: ignore[attr-defined]

    for mod_name in ("stoa_core.rag.ingest", "stoa_core.rag.conversation_memory"):
        mod = importlib.import_module(mod_name)
        mod.bump_kb_version = _stub_bump  # type: ignore[attr-defined]

    print("Using in-memory Redis stub for demo seed (no local Redis required)")


def enable_demo_embeddings() -> None:
    import importlib

    import stoa_core.ingestion.embed as embed_mod

    embed_mod.embed_texts = _demo_embed_texts  # type: ignore[assignment]
    ingest_mod = importlib.import_module("stoa_core.rag.ingest")
    ingest_mod.embed_texts = _demo_embed_texts  # type: ignore[attr-defined]
    print("Using deterministic demo embeddings (no Vertex/OpenAI auth required)")


def _load_env_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {path}")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ[key.strip()] = val.strip().strip('"').strip("'")


def _load_manifest() -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML required: pip install pyyaml") from exc
    return yaml.safe_load(MANIFEST_PATH.read_text())


def _read_demo_file(rel_path: str) -> str:
    path = DEMO_ROOT / rel_path
    return path.read_text(encoding="utf-8")


def _hours_ago(hours: float) -> str:
    return (datetime.now(UTC) - timedelta(hours=hours)).isoformat()


def _days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def ensure_demo_user(sb: Any, manifest: dict[str, Any]) -> str:
    user_cfg = manifest["demo_user"]
    email = os.getenv("DEMO_USER_EMAIL", user_cfg["email"])
    password = os.getenv("DEMO_USER_PASSWORD", user_cfg["password"])
    full_name = user_cfg.get("full_name", "Demo User")

    user_id: str | None = None
    try:
        users_response = sb.auth.admin.list_users()
        users_list = getattr(users_response, "users", users_response) or []
        for u in users_list:
            if getattr(u, "email", None) == email:
                user_id = u.id
                break
    except Exception:
        pass

    if user_id:
        sb.auth.admin.update_user_by_id(user_id, {"password": password, "email_confirm": True})
        print(f"Updated demo user: {email}")
    else:
        created = sb.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        )
        user_id = created.user.id
        print(f"Created demo user: {email}")

    sb.table("user_profiles").upsert(
        {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "onboarding_completed_at": datetime.now(UTC).isoformat(),
        },
        on_conflict="user_id",
    ).execute()
    return user_id


def _normalize_org_profile(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(profile)
    goals = normalized.get("goals")
    if isinstance(goals, list):
        normalized["goals"] = "; ".join(str(g).strip() for g in goals if str(g).strip())
    return normalized


def ensure_org(sb: Any, manifest: dict[str, Any], *, reuse: bool) -> str:
    org_cfg = manifest["org"]
    slug = org_cfg["slug"]
    profile = _normalize_org_profile(org_cfg.get("profile", {}))
    org_payload = {
        "name": org_cfg["name"],
        "website_url": org_cfg.get("website_url"),
        "industry": org_cfg.get("industry"),
        "profile": profile,
        "onboarding_completed_at": datetime.now(UTC).isoformat(),
    }

    if reuse:
        res = sb.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if res.data:
            org_id = res.data[0]["id"]
            sb.table("organizations").update(org_payload).eq("id", org_id).execute()
            print(f"Reusing org: {org_cfg['name']} ({org_id})")
            return org_id

    res = (
        sb.table("organizations")
        .insert(
            {
                "slug": slug,
                **org_payload,
            }
        )
        .execute()
    )
    org_id = res.data[0]["id"]
    print(f"Created org: {org_cfg['name']} ({org_id})")
    return org_id


def ensure_membership(sb: Any, org_id: str, user_id: str) -> None:
    from stoa_core.org.roles import seed_system_roles_for_org

    existing = sb.table("org_roles").select("id, role_key").eq("org_id", org_id).execute()
    if existing.data:
        roles = {r["role_key"]: r["id"] for r in existing.data}
    else:
        roles = seed_system_roles_for_org(sb, org_id, created_by=user_id)
    owner_role_id = roles.get("owner")
    sb.table("memberships").upsert(
        {
            "org_id": org_id,
            "user_id": user_id,
            "role": "owner",
            "role_id": owner_role_id,
        },
        on_conflict="org_id,user_id",
    ).execute()
    sb.table("user_profiles").update({"last_active_org_id": org_id}).eq("user_id", user_id).execute()
    print("Owner membership and roles configured")


def seed_company_profile_kb(org_id: str, manifest: dict[str, Any], *, skip_embeddings: bool) -> None:
    if skip_embeddings:
        return
    from stoa_core.rag.ingest import ingest_knowledge, profile_to_knowledge_text

    org_row = {
        "name": manifest["org"]["name"],
        "website_url": manifest["org"].get("website_url"),
        "industry": manifest["org"].get("industry"),
        "profile": manifest["org"].get("profile", {}),
    }
    text = profile_to_knowledge_text(org_row)
    ingest_knowledge(
        org_id,
        kind="company_profile",
        title=f"{manifest['org']['name']} company profile",
        text=text,
        feature_origin="demo_seed",
        uri="stoa-demo:company_profile",
    )


def seed_integrations(sb: Any, org_id: str, manifest: dict[str, Any]) -> dict[str, str]:
    conn_ids: dict[str, str] = {}
    for item in manifest.get("integrations", []):
        provider = item["provider"]
        last_sync = _hours_ago(item.get("last_sync_hours_ago", 24))
        row = {
            "org_id": org_id,
            "provider": provider,
            "status": item.get("status", "active"),
            "label": item.get("label", provider),
            "provider_metadata": item.get("provider_metadata", {}),
            "last_sync_at": last_sync,
            "credentials_encrypted": None,
        }
        res = sb.table("integration_connections").upsert(row, on_conflict="org_id,provider").execute()
        conn = (res.data or [None])[0]
        if conn:
            conn_ids[provider] = conn["id"]
            sb.table("integration_sync_runs").insert(
                {
                    "org_id": org_id,
                    "connection_id": conn["id"],
                    "status": "completed",
                    "records_fetched": 120,
                    "records_written": 95,
                    "started_at": last_sync,
                    "finished_at": last_sync,
                }
            ).execute()
    print(f"Seeded {len(conn_ids)} integration connections")
    return conn_ids


def seed_crm(org_id: str, manifest: dict[str, Any], *, skip_embeddings: bool, skip_llm_extract: bool) -> None:
    from stoa_core.integrations.store import upsert_account, upsert_contact, upsert_deal, upsert_interaction

    account_ids: dict[str, str] = {}
    for acc in manifest.get("accounts", []):
        saved = upsert_account(
            org_id,
            {
                "external_source": "hubspot",
                "external_id": acc["external_id"],
                "name": acc["name"],
                "domain": acc.get("domain"),
                "industry": acc.get("industry"),
                "lifecycle_stage": acc.get("lifecycle_stage"),
            },
        ) if not skip_embeddings else None
        if skip_embeddings:
            sb = _sb()
            res = sb.table("canonical_accounts").upsert(
                {
                    "org_id": org_id,
                    "external_source": "hubspot",
                    "external_id": acc["external_id"],
                    "name": acc["name"],
                    "domain": acc.get("domain"),
                    "industry": acc.get("industry"),
                    "lifecycle_stage": acc.get("lifecycle_stage"),
                },
                on_conflict="org_id,external_source,external_id",
            ).execute()
            saved = (res.data or [None])[0]
        if saved:
            account_ids[acc["external_id"]] = saved.get("id", acc["external_id"])

    for con in manifest.get("contacts", []):
        row = {
            "external_source": "hubspot",
            "external_id": con["external_id"],
            "name": con["name"],
            "email": con.get("email"),
            "title": con.get("title"),
            "lead_source": con.get("lead_source"),
            "utm_campaign": con.get("utm_campaign"),
            "utm_source": con.get("utm_source"),
            "utm_medium": con.get("utm_medium"),
        }
        if not skip_embeddings:
            upsert_contact(org_id, row)
        else:
            sb = _sb()
            sb.table("canonical_contacts").upsert(
                {**row, "org_id": org_id},
                on_conflict="org_id,external_source,external_id",
            ).execute()

    for deal in manifest.get("deals", []):
        row = {
            "external_source": "hubspot",
            "external_id": deal["external_id"],
            "name": deal["name"],
            "amount": deal.get("amount"),
            "stage": deal.get("stage"),
            "close_date": deal.get("close_date"),
            "is_won": deal.get("is_won"),
            "is_closed": deal.get("is_closed"),
            "loss_reason": deal.get("loss_reason"),
            "lead_source": deal.get("lead_source"),
            "utm_campaign": deal.get("utm_campaign"),
        }
        if not skip_embeddings:
            upsert_deal(org_id, row)
        else:
            sb = _sb()
            sb.table("canonical_deals").upsert(
                {**row, "org_id": org_id},
                on_conflict="org_id,external_source,external_id",
            ).execute()

    for inter in manifest.get("interactions", []):
        body = inter.get("body")
        if not body and inter.get("file"):
            body = _read_demo_file(inter["file"])
        if not body:
            body = inter.get("body", "")
        row = {
            "external_source": inter.get("source", "gong"),
            "external_id": inter["external_id"],
            "interaction_type": inter["type"],
            "title": inter["title"],
            "body_text": body,
        }
        if not skip_embeddings:
            upsert_interaction(org_id, row, extract=not skip_llm_extract)
        else:
            sb = _sb()
            sb.table("canonical_interactions").upsert(
                {**row, "org_id": org_id},
                on_conflict="org_id,external_source,external_id",
            ).execute()

    print("Seeded canonical CRM entities")


def seed_documents(
    org_id: str,
    user_id: str,
    manifest: dict[str, Any],
    *,
    skip_embeddings: bool,
    skip_llm_extract: bool,
) -> None:
    from stoa_core.db.supabase import get_supabase_admin
    from stoa_core.ingestion.chunk import chunk_text
    from stoa_core.ingestion.extract import extract_signals
    from stoa_core.rag.ingest import ingest_knowledge
    from stoa_core.security.pii import redact_pii
    from stoa_core.security.sanitize import sanitize_user_content

    sb = get_supabase_admin()
    seen_titles: set[str] = set()

    for doc_cfg in manifest.get("documents", []):
        title = doc_cfg["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        content = sanitize_user_content(_read_demo_file(doc_cfg["file"]))
        doc_type = doc_cfg["doc_type"]

        existing = (
            sb.table("documents")
            .select("id")
            .eq("org_id", org_id)
            .eq("title", title)
            .limit(1)
            .execute()
        )
        if existing.data:
            doc_id = existing.data[0]["id"]
            sb.table("documents").update({"content": content, "status": "processed"}).eq("id", doc_id).execute()
        else:
            doc_res = (
                sb.table("documents")
                .insert(
                    {
                        "org_id": org_id,
                        "title": title,
                        "doc_type": doc_type,
                        "content": content,
                        "status": "processed",
                        "created_by": user_id,
                    }
                )
                .execute()
            )
            doc_id = doc_res.data[0]["id"]

        if skip_embeddings:
            continue

        text = redact_pii(content)
        ingest_knowledge(
            org_id,
            kind="document",
            title=title,
            text=text,
            feature_origin="demo_seed",
            uri=f"document:{doc_id}",
            metadata={"document_id": doc_id, "doc_type": doc_type},
        )
        for chunk in chunk_text(text):
            chunk_id = str(uuid.uuid4())
            if skip_llm_extract:
                continue
            for signal in extract_signals(redact_pii(chunk.content), doc_id):
                sb.table("intelligence").insert(
                    {
                        "org_id": org_id,
                        "document_id": doc_id,
                        "chunk_id": chunk_id,
                        "kind": signal.get("kind"),
                        "content": redact_pii(signal.get("content") or ""),
                        "confidence": signal.get("confidence", 0.5),
                        "evidence": {"quote": redact_pii(signal.get("evidence_quote", "") or "")},
                    }
                ).execute()

    print("Seeded documents" + (" and intelligence signals" if not skip_llm_extract else ""))


def seed_knowledge(org_id: str, manifest: dict[str, Any], *, skip_embeddings: bool) -> None:
    if skip_embeddings:
        return
    from stoa_core.rag.ingest import ingest_knowledge

    for item in manifest.get("knowledge", []):
        text = _read_demo_file(item["file"])
        ingest_knowledge(
            org_id,
            kind=item["kind"],
            title=item["title"],
            text=text,
            feature_origin="demo_seed",
            uri=item["uri"],
            metadata={"demo": True},
        )
    print("Seeded knowledge chunks")


def seed_competitors(sb: Any, org_id: str, user_id: str, manifest: dict[str, Any]) -> dict[str, str]:
    comp_ids: dict[str, str] = {}
    for comp in manifest.get("competitors", []):
        slug = comp["slug"]
        existing = (
            sb.table("competitors")
            .select("id")
            .eq("org_id", org_id)
            .eq("name", comp["name"])
            .limit(1)
            .execute()
        )
        row = {
            "org_id": org_id,
            "name": comp["name"],
            "website_url": comp.get("website_url"),
            "pricing_url": comp.get("pricing_url"),
            "last_scanned_at": _days_ago(comp.get("last_scanned_days_ago", 3)),
            "created_by": user_id,
        }
        if existing.data:
            comp_id = existing.data[0]["id"]
            sb.table("competitors").update(row).eq("id", comp_id).execute()
        else:
            comp_id = sb.table("competitors").insert(row).execute().data[0]["id"]
        comp_ids[slug] = comp_id

    for alert in manifest.get("competitive_alerts", []):
        comp_id = comp_ids.get(alert["competitor"])
        if not comp_id:
            continue
        existing = (
            sb.table("competitive_alerts")
            .select("id")
            .eq("org_id", org_id)
            .eq("competitor_id", comp_id)
            .eq("summary", alert["summary"])
            .limit(1)
            .execute()
        )
        if existing.data:
            continue
        sb.table("competitive_alerts").insert(
            {
                "org_id": org_id,
                "competitor_id": comp_id,
                "summary": alert["summary"],
                "severity": alert.get("severity", "medium"),
                "categories": alert.get("categories", []),
            }
        ).execute()

    print(f"Seeded {len(comp_ids)} competitors and alerts")
    return comp_ids


def seed_campaigns(sb: Any, org_id: str, user_id: str, manifest: dict[str, Any]) -> dict[str, str]:
    camp_ids: dict[str, str] = {}
    for camp in manifest.get("campaigns", []):
        slug = camp["slug"]
        existing = (
            sb.table("campaigns")
            .select("id")
            .eq("org_id", org_id)
            .eq("brief", camp["brief"])
            .limit(1)
            .execute()
        )
        row = {
            "org_id": org_id,
            "brief": camp["brief"],
            "status": camp["status"],
            "assets": camp.get("assets", {}),
            "error": camp.get("error"),
            "created_by": user_id,
        }
        if existing.data:
            camp_id = existing.data[0]["id"]
            sb.table("campaigns").update(row).eq("id", camp_id).execute()
        else:
            camp_id = sb.table("campaigns").insert(row).execute().data[0]["id"]
        camp_ids[slug] = camp_id
    print(f"Seeded {len(camp_ids)} campaigns")
    return camp_ids


def seed_content_assets(sb: Any, org_id: str, user_id: str, manifest: dict[str, Any]) -> None:
    existing_count = (
        sb.table("content_assets").select("id", count="exact").eq("org_id", org_id).execute()
    )
    if (existing_count.count or 0) >= len(manifest.get("content_assets", [])):
        print("Content assets already seeded — skipping")
        return

    for asset in manifest.get("content_assets", []):
        meta: dict[str, Any] = {}
        if asset.get("generation_time_seconds"):
            meta["generation_time_seconds"] = asset["generation_time_seconds"]
        sb.table("content_assets").insert(
            {
                "org_id": org_id,
                "asset_type": asset["asset_type"],
                "prompt": asset["prompt"],
                "status": asset["status"],
                "error": asset.get("error"),
                "generation_metadata": meta,
                "created_by": user_id,
            }
        ).execute()
    print("Seeded content assets")


def seed_analytics(org_id: str, conn_ids: dict[str, str], manifest: dict[str, Any]) -> None:
    from datetime import date

    from stoa_core.analytics.store import upsert_metric_facts_batch

    period_end = date.today()
    period_start = period_end - timedelta(days=30)
    rows = [
        {
            "dimension_type": r["dimension_type"],
            "dimension_value": r["dimension_value"],
            "metrics": r["metrics"],
        }
        for r in manifest.get("analytics_metrics", [])
    ]
    upsert_metric_facts_batch(
        org_id,
        connection_id=conn_ids.get("ga4"),
        source="ga4",
        period_start=period_start,
        period_end=period_end,
        rows=rows,
    )
    print("Seeded analytics metric facts")


def seed_static_precomputed_insights(org_id: str) -> None:
    """Fallback canned insights when LLM precompute is unavailable."""
    sb = _sb()
    doc_count = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    count = doc_count.count or 0

    static: list[tuple[str, str, str, str]] = [
        (
            "intelligence",
            "top_converting_customers",
            "Who are our highest-converting customers?",
            "FinTech SaaS companies (50–500 employees) convert best, especially webinar-sourced "
            "deals like Acme FinTech ($85k) and CloudLedger ($62k). Partner referrals also close "
            "at high rates.",
        ),
        (
            "intelligence",
            "top_pain_points",
            "What are the top customer pain points?",
            "Manual campaign reporting across HubSpot and GA4, sales-marketing misalignment on "
            "lead quality, and competitive pricing pressure from InsightLoop.",
        ),
        (
            "intelligence",
            "common_objections",
            "What objections come up most in sales?",
            "We already have HubSpot dashboards; implementation time before board meetings; "
            "price comparisons after InsightLoop's 20% discount.",
        ),
        (
            "intelligence",
            "buying_triggers",
            "What triggers customers to buy?",
            "New CMO hire, missed quarterly pipeline targets, and board requests for attribution proof.",
        ),
        (
            "intelligence",
            "win_loss_themes",
            "What win/loss themes stand out?",
            "Wins: faster time-to-insight with Gong + HubSpot evidence. Losses: budget freezes "
            "and InsightLoop price cuts (RevOps Labs, PayStream).",
        ),
        (
            "dashboard",
            "executive_summary",
            "Executive Summary",
            "Stoa demo pipeline shows FinTech as top segment. Webinar leads convert at 38% vs "
            "12% for paid social. InsightLoop pricing change is the top competitive threat. "
            "Q3 launch campaign completed; partner co-marketing failed on missing assets.",
        ),
        (
            "campaign_analysis",
            "top_converting_channels",
            "Which channels convert best?",
            "Email and referral channels convert highest. Organic search drives volume. "
            "Paid social has high sessions but low conversion.",
        ),
        (
            "campaign_analysis",
            "best_vs_worst_campaign",
            "Best vs worst performing campaigns",
            "q3-launch: 24 conversions from 420 sessions. webinar-june: 19 conversions from 185 "
            "sessions (best rate). retargeting-fall: 6 conversions from 290 sessions.",
        ),
        (
            "alignment",
            "leads_that_convert",
            "Which lead sources actually close?",
            "Webinar leads close at ~38% win rate. Partner referrals ~35%. Paid social ~12%.",
        ),
        (
            "alignment",
            "marketing_sales_friction",
            "Where do marketing and sales disagree?",
            "Sales disputes paid social lead quality; marketing cites volume. BrightHR deal "
            "stalled 21 days in Proposal awaiting webinar ROI proof.",
        ),
    ]

    for scope, key, title, answer in static:
        sb.table("precomputed_insights").upsert(
            {
                "org_id": org_id,
                "scope": scope,
                "key": key,
                "title": title,
                "content": {"answer": answer},
                "citations": [],
                "is_stale": key != "message_effectiveness",
                "source_document_count": count,
            },
            on_conflict="org_id,scope,key",
        ).execute()

    sb.table("precomputed_insights").update({"is_stale": True}).eq("org_id", org_id).eq(
        "scope", "campaign_analysis"
    ).eq("key", "message_effectiveness").execute()
    print("Seeded static precomputed insights (LLM fallback)")


def run_precompute(org_id: str, *, skip_embeddings: bool) -> None:
    if skip_embeddings:
        print("Skipping precompute (--skip-embeddings)")
        return

    from stoa_core.analytics.synthesize import precompute_campaign_answers
    from stoa_core.alignment.synthesize import precompute_alignment_answers
    from stoa_core.insights.common import build_executive_summary, precompute_answers
    from stoa_core.db.supabase import get_supabase_admin

    sb = get_supabase_admin()
    doc_count = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    count = doc_count.count or 0

    def upsert(scope: str, item: dict[str, Any]) -> None:
        sb.table("precomputed_insights").upsert(
            {
                "org_id": org_id,
                "scope": scope,
                "key": item["key"],
                "title": item["title"],
                "content": item["content"],
                "citations": item.get("citations", []),
                "is_stale": False,
                "source_document_count": count,
            },
            on_conflict="org_id,scope,key",
        ).execute()

    print("Running intelligence precompute (may call LLM)...")
    try:
        for item in precompute_answers(org_id):
            upsert("intelligence", item)

        org_name = "Stoa"
        exec_summary = build_executive_summary(org_id, org_name)
        if exec_summary.get("summary"):
            upsert(
                "dashboard",
                {
                    "key": "executive_summary",
                    "title": "Executive Summary",
                    "content": exec_summary,
                    "citations": exec_summary.get("citations", []),
                },
            )

        print("Running campaign analysis precompute...")
        for item in precompute_campaign_answers(org_id):
            upsert("campaign_analysis", item)

        print("Running alignment precompute...")
        for item in precompute_alignment_answers(org_id):
            upsert("alignment", item)

        sb.table("precomputed_insights").update({"is_stale": True}).eq("org_id", org_id).eq(
            "scope", "campaign_analysis"
        ).eq("key", "message_effectiveness").execute()
        print("Precompute complete")
    except Exception as exc:
        print(f"LLM precompute failed ({exc}); using static insight fallback")
        seed_static_precomputed_insights(org_id)


def _sb() -> Any:
    from stoa_core.db.supabase import get_supabase_admin

    return get_supabase_admin()


def _auth_users(sb: Any) -> list[Any]:
    users: list[Any] = []
    page = 1
    while True:
        response = sb.auth.admin.list_users(page=page, per_page=200)
        batch = response if isinstance(response, list) else getattr(response, "users", None) or []
        if not batch:
            break
        users.extend(batch)
        if len(batch) < 200:
            break
        page += 1
    return users


def wipe_workspace(sb: Any) -> None:
    """Delete all organizations and auth users (dev/demo reset only)."""
    orgs = sb.table("organizations").select("id,name,slug").execute().data or []
    for org in orgs:
        sb.table("organizations").delete().eq("id", org["id"]).execute()
        print(f"Deleted org: {org.get('name')} ({org.get('slug')})")

    for user in _auth_users(sb):
        email = getattr(user, "email", None) or user.get("email") if isinstance(user, dict) else None
        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        if not user_id:
            continue
        sb.auth.admin.delete_user(str(user_id))
        print(f"Deleted user: {email or user_id}")

    remaining_orgs = sb.table("organizations").select("id", count="exact").execute().count or 0
    remaining_users = len(_auth_users(sb))
    if remaining_orgs or remaining_users:
        raise SystemExit(
            f"Workspace wipe incomplete ({remaining_orgs} orgs, {remaining_users} users remaining)"
        )
    print("Workspace wiped: 0 orgs, 0 auth users")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Stoa demo workspace")
    parser.add_argument("--reuse", action="store_true", help="Reuse existing org by slug")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete all orgs and auth users, then seed a new demo workspace",
    )
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip KB ingest and precompute")
    parser.add_argument("--env-file", default=None, help="Load env vars from file (e.g. .env.staging)")
    parser.add_argument(
        "--offline-redis",
        action="store_true",
        help="Use in-memory Redis stub when local Redis is unavailable",
    )
    parser.add_argument(
        "--demo-embeddings",
        action="store_true",
        help="Use deterministic pseudo-embeddings when cloud providers are unavailable",
    )
    parser.add_argument(
        "--with-llm-extract",
        action="store_true",
        help="Run live LLM signal extraction during seed (slow; demo uses pre-authored KB + static insights)",
    )
    args = parser.parse_args()
    if args.fresh and args.reuse:
        raise SystemExit("Use either --fresh or --reuse, not both")

    default_env = REPO_ROOT / "services" / "api" / ".env"
    env_path = Path(args.env_file) if args.env_file else default_env if default_env.exists() else REPO_ROOT / ".env"
    if env_path.exists():
        _load_env_file(env_path)
        print(f"Loaded env from {env_path}")

    os.environ.setdefault("STOA_ENV", "development")

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    if args.offline_redis:
        enable_offline_seed_mode()
    if args.demo_embeddings:
        enable_demo_embeddings()

    skip_llm_extract = not args.with_llm_extract
    if skip_llm_extract:
        print("Skipping live LLM signal extraction (use --with-llm-extract to enable)")

    manifest = _load_manifest()
    from supabase import create_client

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

    if args.fresh:
        print("=== Wiping existing workspace ===")
        wipe_workspace(sb)

    user_id = ensure_demo_user(sb, manifest)
    org_id = ensure_org(sb, manifest, reuse=args.reuse and not args.fresh)
    ensure_membership(sb, org_id, user_id)

    seed_company_profile_kb(org_id, manifest, skip_embeddings=args.skip_embeddings)
    conn_ids = seed_integrations(sb, org_id, manifest)
    seed_crm(org_id, manifest, skip_embeddings=args.skip_embeddings, skip_llm_extract=skip_llm_extract)
    seed_documents(
        org_id,
        user_id,
        manifest,
        skip_embeddings=args.skip_embeddings,
        skip_llm_extract=skip_llm_extract,
    )
    seed_knowledge(org_id, manifest, skip_embeddings=args.skip_embeddings)
    seed_competitors(sb, org_id, user_id, manifest)
    seed_campaigns(sb, org_id, user_id, manifest)
    seed_content_assets(sb, org_id, user_id, manifest)
    seed_analytics(org_id, conn_ids, manifest)
    run_precompute(org_id, skip_embeddings=args.skip_embeddings)

    email = os.getenv("DEMO_USER_EMAIL", manifest["demo_user"]["email"])
    password = os.getenv("DEMO_USER_PASSWORD", manifest["demo_user"]["password"])

    print("\n=== Demo workspace ready ===")
    print(f"Org ID:      {org_id}")
    print(f"Org name:    {manifest['org']['name']}")
    print(f"Login email: {email}")
    print(f"Password:    {password}")
    print("App:         http://localhost:3000 (or your deployed URL)")
    print("Docs:        docs/demo/VIDEO_SCRIPT.md")


if __name__ == "__main__":
    main()
