"""Legacy dashboard feature tools (ICP, campaigns, competitive, etc.)."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool

from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.friction import collect_friction_signals
from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.intelligence.structured import aggregate_crm_stats


def _as_rows(data: Any) -> list[dict[str, Any]]:
    if not data:
        return []
    return [r for r in data if isinstance(r, dict)]


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, default=str)


def _get_precomputed_insights(org_id: str, scope: str, limit: int = 8) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("key, title, content, citations, is_stale, updated_at")
        .eq("org_id", org_id)
        .eq("scope", scope)
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _as_rows(res.data)


def build_dashboard_tools(org_id: str) -> list[StructuredTool]:
    def icp_customer_research_tool(query: str) -> str:
        """Answer ICP and customer research questions from CRM + intelligence insights."""
        stats = aggregate_crm_stats(org_id)
        insights = _get_precomputed_insights(org_id, "intelligence", limit=8)
        best_segment = (stats.get("top_industries") or [{}])[0]
        payload = {
            "feature": "icp_customer_research",
            "query": query,
            "highlights": {
                "best_customer_segment": best_segment.get("name"),
                "total_deals": stats.get("total_deals", 0),
                "win_rate_percent": stats.get("win_rate_percent"),
                "top_loss_reasons": stats.get("top_loss_reasons", []),
            },
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    def content_bottleneck_tool(query: str) -> str:
        """Return content generation bottlenecks and throughput metrics."""
        sb = get_supabase_admin()
        rows = _as_rows(
            (
                sb.table("content_assets")
                .select(
                    "id, status, asset_type, generation_metadata, created_at, updated_at, error"
                )
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(300)
                .execute()
            ).data
        )

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        durations: list[float] = []
        failed_examples: list[dict[str, Any]] = []

        for row in rows:
            status = str(row.get("status") or "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            asset_type = str(row.get("asset_type") or "unknown")
            by_type[asset_type] = by_type.get(asset_type, 0) + 1

            metadata = row.get("generation_metadata") or {}
            if isinstance(metadata, dict):
                raw = metadata.get("generation_time_seconds")
                if isinstance(raw, int | float):
                    durations.append(float(raw))

            if status == "failed" and len(failed_examples) < 5:
                failed_examples.append(
                    {
                        "id": row.get("id"),
                        "error": row.get("error"),
                        "created_at": row.get("created_at"),
                    }
                )

        avg_duration = round(sum(durations) / len(durations), 2) if durations else None
        payload = {
            "feature": "content_bottleneck",
            "query": query,
            "metrics": {
                "total_assets": len(rows),
                "status_breakdown": by_status,
                "asset_type_breakdown": by_type,
                "avg_generation_time_seconds": avg_duration,
                "failed_examples": failed_examples,
            },
        }
        return _json(payload)

    def competitive_intelligence_tool(query: str) -> str:
        """Return competitor coverage and latest competitive alerts."""
        sb = get_supabase_admin()
        competitors = _as_rows(
            (
                sb.table("competitors")
                .select("id, name, website_url, pricing_url, last_scanned_at")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            ).data
        )
        alerts = _as_rows(
            (
                sb.table("competitive_alerts")
                .select("id, summary, severity, categories, created_at, competitor_id")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            ).data
        )

        severity_counts: dict[str, int] = {}
        for a in alerts:
            sev = str(a.get("severity") or "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        payload = {
            "feature": "competitive_intelligence",
            "query": query,
            "metrics": {
                "tracked_competitors": len(competitors),
                "recent_alerts": len(alerts),
                "alerts_by_severity": severity_counts,
                "latest_alerts": alerts[:10],
            },
        }
        return _json(payload)

    def launch_orchestration_tool(query: str) -> str:
        """Return launch orchestration status based on campaign pipeline state."""
        sb = get_supabase_admin()
        campaigns = _as_rows(
            (
                sb.table("campaigns")
                .select("id, brief, status, created_at, updated_at, error")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(120)
                .execute()
            ).data
        )

        status_counts: dict[str, int] = {}
        for c in campaigns:
            status = str(c.get("status") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        payload = {
            "feature": "launch_orchestration",
            "query": query,
            "metrics": {
                "campaign_count": len(campaigns),
                "status_breakdown": status_counts,
                "latest_campaigns": campaigns[:8],
            },
            "note": (
                "Use the dedicated campaigns flow for creation/execution operations; "
                "this tool focuses on orchestration intelligence and status visibility."
            ),
        }
        return _json(payload)

    def campaign_analysis_tool(query: str) -> str:
        """Return campaign/channel performance insights and comparisons."""
        metrics = build_summary_metrics(org_id)
        insights = _get_precomputed_insights(org_id, "campaign_analysis", limit=8)
        payload = {
            "feature": "campaign_analysis",
            "query": query,
            "metrics": metrics,
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    def sales_marketing_alignment_tool(query: str) -> str:
        """Return sales-marketing alignment metrics, friction signals, and insights."""
        summary = build_alignment_summary(org_id)
        friction = collect_friction_signals(org_id)
        insights = _get_precomputed_insights(org_id, "alignment", limit=8)
        payload = {
            "feature": "sales_marketing_alignment",
            "query": query,
            "alignment": summary,
            "friction": friction,
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    return [
        StructuredTool.from_function(icp_customer_research_tool),
        StructuredTool.from_function(content_bottleneck_tool),
        StructuredTool.from_function(competitive_intelligence_tool),
        StructuredTool.from_function(launch_orchestration_tool),
        StructuredTool.from_function(campaign_analysis_tool),
        StructuredTool.from_function(sales_marketing_alignment_tool),
    ]
