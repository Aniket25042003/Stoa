"""
File: services/core/src/stoa_core/integrations/posthog.py
Layer: Core Integration Connectors
Purpose: Implements posthog behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import httpx

from stoa_core.analytics.store import upsert_metric_facts_batch
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_posthog_projects
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "posthog"

_UTM_BREAKDOWNS = [
    ("utm_campaign", "$utm_campaign"),
    ("utm_source", "$utm_source"),
    ("utm_medium", "$utm_medium"),
]


@register_connector
class PosthogConnector(BaseConnector):
    """Manage PosthogConnector behavior within the Stoa application layer."""
    provider = "posthog"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="posthog",
            name="PostHog",
            auth_type="api_key",
            description="Import aggregated product usage summaries from PostHog.",
            resource_selection_mode="required",
            resource_kinds=["project"],
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise ValueError("PostHog api_key is required")
        host = credentials.get("host", "https://app.posthog.com").rstrip("/")
        return {"api_key": api_key, "provider_metadata": {"host": host}}

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return list_posthog_projects(credentials, metadata)

    @classmethod
    def _fetch_trend(
        cls,
        *,
        host: str,
        project_id: str,
        headers: dict[str, str],
        breakdown: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "events": json.dumps([{"id": "$pageview"}]),
            "date_from": "-30d",
        }
        if breakdown:
            params["breakdown"] = breakdown
            params["breakdown_type"] = "event"
        with httpx.Client(timeout=60) as client:
            res = client.get(
                f"{host}/api/projects/{project_id}/insights/trend/",
                headers=headers,
                params=params,
            )
            if res.status_code >= 400:
                return []
            return res.json().get("result") or []

    @classmethod
    def sync(
        cls,
        org_id: str,
        connection: dict[str, Any],
        *,
        credentials: dict[str, Any],
        cursor: dict[str, Any],
        full_backfill: bool = False,
    ) -> SyncResult:
        result = SyncResult()
        metadata = connection.get("provider_metadata") or {}
        project_id = metadata.get("project_id")
        if not project_id:
            result.error = "No PostHog project selected — configure access first"
            return result
        host = metadata.get("host", "https://app.posthog.com")
        connection_id = connection.get("id")
        headers = {"Authorization": f"Bearer {credentials['api_key']}"}
        period_end = date.today()
        period_start = period_end - timedelta(days=30)

        try:
            all_metric_rows: list[dict[str, Any]] = []
            summary_lines = ["# PostHog Usage Summary (last 30 days)", ""]

            overall = cls._fetch_trend(host=host, project_id=project_id, headers=headers)
            for series in overall:
                label = series.get("label") or series.get("action", {}).get("name") or "event"
                data = series.get("data") or []
                total = sum(data) if data else 0
                summary_lines.append(f"- {label}: {total} events")
                all_metric_rows.append(
                    {
                        "dimension_type": "channel",
                        "dimension_value": str(label),
                        "metrics": {"events": total, "sessions": total},
                    }
                )

            for dimension_type, breakdown_prop in _UTM_BREAKDOWNS:
                series_list = cls._fetch_trend(
                    host=host,
                    project_id=project_id,
                    headers=headers,
                    breakdown=breakdown_prop,
                )
                for series in series_list:
                    label = series.get("label") or "(not set)"
                    data = series.get("data") or []
                    total = sum(data) if data else 0
                    if total <= 0:
                        continue
                    all_metric_rows.append(
                        {
                            "dimension_type": dimension_type,
                            "dimension_value": str(label),
                            "metrics": {"events": total, "sessions": total},
                        }
                    )

            written = upsert_metric_facts_batch(
                org_id,
                connection_id=connection_id,
                source=SOURCE,
                period_start=period_start,
                period_end=period_end,
                rows=all_metric_rows,
            )

            text = "\n".join(summary_lines) if len(summary_lines) > 2 else "# PostHog: no trend data returned"
            ingest_knowledge(
                org_id,
                kind="product_analytics_summary",
                title="PostHog usage summary",
                text=text,
                feature_origin="integrations",
                uri=f"posthog:summary:{project_id}",
                metadata={"source": SOURCE},
            )
            ingest_knowledge(
                org_id,
                kind="campaign_metrics",
                title="PostHog campaign metrics snapshot",
                text=text,
                feature_origin="integrations",
                uri=f"posthog:metrics:{project_id}:{period_end.isoformat()}",
                metadata={"source": SOURCE, "period_end": period_end.isoformat()},
            )

            result.records_fetched = len(all_metric_rows)
            result.records_written = written + 2
            result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("PostHog sync failed for org %s", org_id)
            result.error = str(exc)

        return result

    @classmethod
    def supports_agent_search(cls) -> bool:
        return True

    @classmethod
    def agent_search(
        cls,
        org_id: str,
        connection: dict[str, Any],
        *,
        credentials: dict[str, Any],
        query: str,
        entity_type: str | None = None,
    ) -> list:
        from stoa_core.integrations.agent_search import agent_search_hit
        from stoa_core.integrations.base import AgentSearchHit

        metadata = connection.get("provider_metadata") or {}
        project_id = metadata.get("project_id")
        if not project_id:
            return []
        host = metadata.get("host") or credentials.get("host") or "https://app.posthog.com"
        host = str(host).rstrip("/")
        api_key = credentials.get("api_key", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        breakdown = "$utm_campaign" if entity_type in {"campaign", "campaigns"} else None
        rows = cls._fetch_trend(
            host=host,
            project_id=str(project_id),
            headers=headers,
            breakdown=breakdown,
        )
        hits: list[AgentSearchHit] = []
        for row in rows[:15]:
            label = row.get("label") or row.get("breakdown_value") or "segment"
            total = row.get("count") or row.get("aggregated_value") or 0
            hits.append(
                agent_search_hit(
                    id=str(label).replace(" ", "_")[:80],
                    title=f"PostHog: {label}",
                    snippet=f"events={total} (last 30 days)",
                    provider=SOURCE,
                    entity_type=entity_type,
                )
            )
        return hits
