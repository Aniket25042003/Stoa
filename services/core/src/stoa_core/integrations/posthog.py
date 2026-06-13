"""PostHog analytics summary connector."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "posthog"


@register_connector
class PosthogConnector(BaseConnector):
    provider = "posthog"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="posthog",
            name="PostHog",
            auth_type="api_key",
            description="Import aggregated product usage summaries from PostHog.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        api_key = credentials.get("api_key", "").strip()
        project_id = credentials.get("project_id", "").strip()
        if not api_key or not project_id:
            raise ValueError("PostHog api_key and project_id are required")
        host = credentials.get("host", "https://app.posthog.com").rstrip("/")
        return {
            "api_key": api_key,
            "provider_metadata": {"project_id": project_id, "host": host},
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
        result = SyncResult()
        metadata = connection.get("provider_metadata") or {}
        project_id = metadata.get("project_id")
        host = metadata.get("host", "https://app.posthog.com")
        headers = {"Authorization": f"Bearer {credentials['api_key']}"}

        try:
            with httpx.Client(timeout=60) as client:
                res = client.get(
                    f"{host}/api/projects/{project_id}/insights/trend/",
                    headers=headers,
                    params={"events": '[{"id":"$pageview"}]', "date_from": "-30d"},
                )
                if res.status_code >= 400:
                    result.error = f"PostHog API error: {res.status_code}"
                    return result
                body = res.json()

            result.records_fetched = 1
            lines = ["# PostHog Usage Summary (last 30 days)", ""]
            for series in body.get("result") or []:
                label = series.get("label") or series.get("action", {}).get("name") or "event"
                data = series.get("data") or []
                total = sum(data) if data else 0
                lines.append(f"- {label}: {total} events")

            text = "\n".join(lines) if len(lines) > 2 else "# PostHog: no trend data returned"
            ingest_knowledge(
                org_id,
                kind="product_analytics_summary",
                title="PostHog usage summary",
                text=text,
                feature_origin="integrations",
                uri=f"posthog:summary:{project_id}",
                metadata={"source": SOURCE},
            )
            result.records_written = 1
            result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("PostHog sync failed for org %s", org_id)
            result.error = str(exc)

        return result
