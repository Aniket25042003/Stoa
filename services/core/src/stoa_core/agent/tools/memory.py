"""Tier 1 agent tools: workspace memory search and freshness."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import StructuredTool

from stoa_core.agent.evidence import (
    EvidenceHit,
    get_cached_evidence,
    hits_to_tool_json,
    store_conversation_evidence,
)
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.cache import get_kb_version
from stoa_core.rag.query_prepare import retrieve_context_prepared

logger = logging.getLogger(__name__)


def _as_rows(data: Any) -> list[dict[str, Any]]:
    if not data:
        return []
    return [r for r in data if isinstance(r, dict)]


def build_memory_tools(
    org_id: str,
    conversation_id: str,
    *,
    memory_kinds: list[str],
) -> list[StructuredTool]:
    def search_workspace_memory(query: str, kinds: str | None = None) -> str:
        """Run an additional knowledge-base search mid-turn with a refined query."""
        kind_list = [k.strip() for k in (kinds or "").split(",") if k.strip()] or None
        cached = get_cached_evidence(
            org_id,
            conversation_id,
            source="kb",
            query=query,
            entity_type=kinds,
        )
        if cached is not None:
            return hits_to_tool_json(cached, cached=True)

        try:
            context, prepared = retrieve_context_prepared(
                org_id,
                query,
                kinds=kind_list or memory_kinds,
                k=8,
                conversation_id=conversation_id,
            )
        except Exception as exc:
            return json.dumps({"error": str(exc), "count": 0, "hits": []})

        hits: list[EvidenceHit] = []
        for item in context:
            ref = str(item.get("ref") or "")
            text = str(item.get("text") or "")[:2000]
            title = str(item.get("title") or ref or "KB chunk")
            hits.append(
                EvidenceHit(
                    id=ref.replace("kb:", ""),
                    title=title,
                    snippet=text,
                    uri=ref,
                    provider="kb",
                    source="kb",
                    fetched_at=datetime.now(UTC).isoformat(),
                    persist_eligible=False,
                )
            )
        stored = store_conversation_evidence(
            org_id,
            conversation_id,
            source="kb",
            query=query,
            hits=hits,
            entity_type=kinds,
        )
        payload = {
            "cached": False,
            "rewrite_used": prepared.rewrite_used,
            "search_queries": prepared.search_queries,
            "count": len(stored),
            "hits": [
                {
                    "ref": h.uri,
                    "title": h.title,
                    "snippet": h.snippet[:400],
                }
                for h in stored[:12]
            ],
        }
        return json.dumps(payload, default=str)

    def get_workspace_freshness() -> str:
        """Return integration sync times, stale insights, and KB version for this workspace."""
        sb = get_supabase_admin()
        connections = _as_rows(
            (
                sb.table("integration_connections")
                .select("id, provider, status, last_sync_at, last_error, provider_metadata")
                .eq("org_id", org_id)
                .execute()
            ).data
        )
        sync_runs = _as_rows(
            (
                sb.table("integration_sync_runs")
                .select("connection_id, status, started_at, finished_at")
                .eq("org_id", org_id)
                .order("started_at", desc=True)
                .limit(20)
                .execute()
            ).data
        )
        insights = _as_rows(
            (
                sb.table("precomputed_insights")
                .select("scope, key, is_stale, created_at")
                .eq("org_id", org_id)
                .execute()
            ).data
        )
        competitors = _as_rows(
            (
                sb.table("competitors")
                .select("id, name, last_scanned_at")
                .eq("org_id", org_id)
                .order("last_scanned_at", desc=True)
                .limit(10)
                .execute()
            ).data
        )
        evidence = _as_rows(
            (
                sb.table("knowledge_chunks")
                .select("metadata, created_at")
                .eq("org_id", org_id)
                .eq("kind", "agent_search_evidence")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            ).data
        )
        by_provider: dict[str, str] = {}
        for row in evidence:
            meta = row.get("metadata") or {}
            prov = meta.get("provider")
            if prov and prov not in by_provider:
                by_provider[str(prov)] = str(row.get("created_at") or "")

        payload = {
            "kb_version": get_kb_version(org_id),
            "integrations": [
                {
                    "provider": c.get("provider"),
                    "status": c.get("status"),
                    "last_sync_at": c.get("last_sync_at"),
                    "last_error": c.get("last_error"),
                }
                for c in connections
            ],
            "recent_sync_runs": sync_runs[:8],
            "precomputed_insights": [
                {
                    "scope": i.get("scope"),
                    "key": i.get("key"),
                    "is_stale": i.get("is_stale"),
                    "created_at": i.get("created_at"),
                }
                for i in insights
            ],
            "competitors": competitors,
            "agent_search_evidence_by_provider": by_provider,
        }
        return json.dumps(payload, default=str)

    return [
        StructuredTool.from_function(search_workspace_memory),
        StructuredTool.from_function(get_workspace_freshness),
    ]
