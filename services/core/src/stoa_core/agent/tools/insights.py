"""Tier 3 agent tools: async refresh and enrichment."""

from __future__ import annotations

import json

from langchain_core.tools import StructuredTool

from stoa_core.agent.rate_limit import check_refresh_limit
from stoa_core.agent.refresh_enqueue import (
    enqueue_refresh_competitor_intel,
    enqueue_refresh_connected_source,
    enqueue_refresh_precomputed_insights,
)


def build_insights_tools(org_id: str) -> list[StructuredTool]:
    def refresh_connected_source(provider: str, full_backfill: bool = False) -> str:
        """Enqueue a connector sync to pull the latest data into the workspace."""
        if not check_refresh_limit(org_id):
            return json.dumps({"error": "Refresh rate limit exceeded for this hour"})
        result = enqueue_refresh_connected_source(
            org_id, provider.strip().lower(), full_backfill=full_backfill
        )
        if result.get("status") == "queued":
            result["note"] = (
                "Refresh queued — use current evidence and note refresh in progress"
            )
        return json.dumps(result)

    def refresh_precomputed_insights(scope: str | None = None) -> str:
        """Rebuild stale dashboard Q&A insights (intelligence, campaign_analysis, alignment)."""
        if not check_refresh_limit(org_id):
            return json.dumps({"error": "Refresh rate limit exceeded for this hour"})
        result = enqueue_refresh_precomputed_insights(org_id, scope=scope)
        if result.get("status") == "queued":
            result["note"] = "Insight rebuild queued — current precomputed insights may be stale"
        return json.dumps(result)

    def refresh_competitor_intel(competitor_name: str | None = None) -> str:
        """Rescan and enrich intelligence for a tracked competitor."""
        if not check_refresh_limit(org_id):
            return json.dumps({"error": "Refresh rate limit exceeded for this hour"})
        result = enqueue_refresh_competitor_intel(org_id, competitor_name=competitor_name)
        if result.get("status") == "queued":
            result["note"] = "Competitor rescan queued — use current DB alerts until complete"
        return json.dumps(result)

    return [
        StructuredTool.from_function(refresh_connected_source),
        StructuredTool.from_function(refresh_precomputed_insights),
        StructuredTool.from_function(refresh_competitor_intel),
    ]
