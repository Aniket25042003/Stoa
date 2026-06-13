"""Slack channel messages connector (KB enrichment)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "slack"


@register_connector
class SlackConnector(BaseConnector):
    provider = "slack"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="slack",
            name="Slack",
            auth_type="oauth",
            description="Import messages from selected Slack channels into the knowledge base.",
            scopes=["channels:history", "channels:read", "groups:history", "groups:read"],
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        token = credentials.get("access_token", "").strip()
        channels = credentials.get("channel_ids") or []
        if not token:
            raise ValueError("Slack access token is required")
        return {
            "access_token": token,
            "provider_metadata": {"channel_ids": channels},
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
        channel_ids = metadata.get("channel_ids") or credentials.get("channel_ids") or []
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}

        try:
            for channel_id in channel_ids[:5]:
                with httpx.Client(timeout=60) as client:
                    res = client.get(
                        "https://slack.com/api/conversations.history",
                        headers=headers,
                        params={"channel": channel_id, "limit": 100},
                    )
                    res.raise_for_status()
                    body = res.json()
                if not body.get("ok"):
                    continue
                messages = body.get("messages") or []
                result.records_fetched += len(messages)
                lines = [m.get("text", "") for m in messages if m.get("text")]
                if not lines:
                    continue
                text = "\n".join(lines)
                ingest_knowledge(
                    org_id,
                    kind="document",
                    title=f"Slack channel {channel_id}",
                    text=text,
                    feature_origin="integrations",
                    uri=f"slack:channel:{channel_id}",
                    metadata={"source": SOURCE, "channel_id": channel_id},
                )
                result.records_written += 1
            result.cursor = {"stage": "done"}
        except Exception as exc:
            logger.exception("Slack sync failed for org %s", org_id)
            result.error = str(exc)
        return result
