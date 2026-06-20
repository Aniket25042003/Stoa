"""
File: services/core/src/stoa_core/integrations/ga4.py
Layer: Core Integration Connectors
Purpose: Implements ga4 behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "ga4"


@register_connector
class Ga4Connector(BaseConnector):
    """Manage Ga4Connector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "ga4"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="ga4",
            name="Google Analytics 4",
            auth_type="oauth",
            description="Import aggregated traffic and conversion summaries from GA4.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles connect with credentials logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        token = credentials.get("access_token", "").strip()
        property_id = credentials.get("property_id", "").strip()
        if not token or not property_id:
            raise ValueError("GA4 access token and property_id are required")
        return {
            "access_token": token,
            "provider_metadata": {"property_id": property_id},
        }

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
        """Handles sync logic for the surrounding Stoa workflow.

        Args:
            org_id (str): Input value used by this workflow step.
            connection (dict[str, Any]): Input value used by this workflow step.
            credentials (dict[str, Any]): Input value used by this workflow step.
            cursor (dict[str, Any]): Input value used by this workflow step.
            full_backfill (bool): Input value used by this workflow step.

        Returns:
            SyncResult: Result produced for the caller.
        """
        result = SyncResult()
        metadata = connection.get("provider_metadata") or {}
        property_id = metadata.get("property_id")
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}

        try:
            payload = {
                "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
                "dimensions": [{"name": "sessionDefaultChannelGroup"}],
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
                body = res.json()

            rows = body.get("rows") or []
            result.records_fetched = len(rows)
            lines = ["# GA4 Traffic Summary (last 30 days)", ""]
            for row in rows:
                dims = [d.get("value") for d in row.get("dimensionValues") or []]
                metrics = [m.get("value") for m in row.get("metricValues") or []]
                channel = dims[0] if dims else "unknown"
                lines.append(f"- {channel}: sessions={metrics[0] if metrics else 0}, conversions={metrics[1] if len(metrics) > 1 else 0}")

            text = "\n".join(lines)
            ingest_knowledge(
                org_id,
                kind="product_analytics_summary",
                title="GA4 traffic summary",
                text=text,
                feature_origin="integrations",
                uri=f"ga4:summary:{property_id}",
                metadata={"source": SOURCE, "property_id": property_id},
            )
            result.records_written = 1
            result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("GA4 sync failed for org %s", org_id)
            result.error = str(exc)

        return result
