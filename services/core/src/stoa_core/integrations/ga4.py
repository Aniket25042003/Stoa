"""
File: services/core/src/stoa_core/integrations/ga4.py
Layer: Core Integration Connectors
Purpose: Implements ga4 behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from stoa_core.analytics.store import upsert_metric_facts_batch
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.google_oauth import (
    GA4_SCOPE,
    exchange_google_code,
    google_authorize_url,
    google_oauth_configured,
)
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_ga4_properties
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "ga4"

_GA4_REPORTS: list[tuple[str, str]] = [
    ("channel", "sessionDefaultChannelGroup"),
    ("campaign", "sessionCampaignName"),
    ("source_medium", "sessionSourceMedium"),
    ("landing_page", "landingPage"),
]


@register_connector
class Ga4Connector(BaseConnector):
    """Manage Ga4Connector behavior within the Stoa application layer."""
    provider = "ga4"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="ga4",
            name="Google Analytics 4",
            auth_type="oauth",
            description="Import aggregated traffic and conversion summaries from GA4.",
            scopes=[GA4_SCOPE],
            supports_credential_auth=True,
            resource_selection_mode="required",
            resource_kinds=["property"],
        )

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str | None:
        if not google_oauth_configured():
            return None
        return google_authorize_url(state, redirect_uri, [GA4_SCOPE])

    @classmethod
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token_data = exchange_google_code(code, redirect_uri)
        return token_data

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        token = credentials.get("access_token", "").strip()
        if not token:
            raise ValueError("GA4 access token is required")
        return {"access_token": token, "provider_metadata": {}}

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return list_ga4_properties(credentials)

    @classmethod
    def _run_report(
        cls,
        *,
        headers: dict[str, str],
        property_id: str,
        dimension_name: str,
    ) -> list[dict[str, Any]]:
        payload = {
            "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
            "dimensions": [{"name": dimension_name}],
            "metrics": [
                {"name": "sessions"},
                {"name": "conversions"},
                {"name": "totalUsers"},
            ],
        }
        with httpx.Client(timeout=60) as client:
            res = client.post(
                f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
                headers=headers,
                json=payload,
            )
            res.raise_for_status()
            return res.json().get("rows") or []

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
        property_id = metadata.get("property_id")
        if not property_id:
            result.error = "No GA4 property selected — configure access first"
            return result
        connection_id = connection.get("id")
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}
        period_end = date.today()
        period_start = period_end - timedelta(days=30)

        try:
            all_metric_rows: list[dict[str, Any]] = []
            summary_lines = ["# GA4 Traffic Summary (last 30 days)", ""]
            total_fetched = 0

            for dimension_type, dimension_name in _GA4_REPORTS:
                rows = cls._run_report(
                    headers=headers,
                    property_id=property_id,
                    dimension_name=dimension_name,
                )
                total_fetched += len(rows)
                for row in rows:
                    dims = [d.get("value") for d in row.get("dimensionValues") or []]
                    metric_vals = [m.get("value") for m in row.get("metricValues") or []]
                    dim_value = dims[0] if dims else "unknown"
                    sessions = float(metric_vals[0]) if len(metric_vals) > 0 else 0
                    conversions = float(metric_vals[1]) if len(metric_vals) > 1 else 0
                    users = float(metric_vals[2]) if len(metric_vals) > 2 else 0
                    all_metric_rows.append(
                        {
                            "dimension_type": dimension_type,
                            "dimension_value": dim_value,
                            "metrics": {
                                "sessions": sessions,
                                "conversions": conversions,
                                "users": users,
                                "totalUsers": users,
                            },
                        }
                    )
                    if dimension_type == "channel":
                        summary_lines.append(
                            f"- {dim_value}: sessions={int(sessions)}, conversions={int(conversions)}"
                        )

            written = upsert_metric_facts_batch(
                org_id,
                connection_id=connection_id,
                source=SOURCE,
                period_start=period_start,
                period_end=period_end,
                rows=all_metric_rows,
            )

            text = "\n".join(summary_lines)
            ingest_knowledge(
                org_id,
                kind="product_analytics_summary",
                title="GA4 traffic summary",
                text=text,
                feature_origin="integrations",
                uri=f"ga4:summary:{property_id}",
                metadata={"source": SOURCE, "property_id": property_id},
            )
            ingest_knowledge(
                org_id,
                kind="campaign_metrics",
                title="GA4 campaign metrics snapshot",
                text=text,
                feature_origin="integrations",
                uri=f"ga4:metrics:{property_id}:{period_end.isoformat()}",
                metadata={"source": SOURCE, "period_end": period_end.isoformat()},
            )

            result.records_fetched = total_fetched
            result.records_written = written + 2
            result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("GA4 sync failed for org %s", org_id)
            result.error = str(exc)

        return result
