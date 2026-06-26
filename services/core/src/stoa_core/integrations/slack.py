"""
File: services/core/src/stoa_core/integrations/slack.py
Layer: Core Integration Connectors
Purpose: Implements slack behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_slack_channels
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "slack"
SLACK_SCOPES = ["channels:history", "channels:read", "groups:history", "groups:read"]


def _settings():
    return get_settings()


@register_connector
class SlackConnector(BaseConnector):
    """Manage SlackConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "slack"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="slack",
            name="Slack",
            auth_type="oauth",
            description="Import messages from selected Slack channels into the knowledge base.",
            scopes=SLACK_SCOPES,
            supports_credential_auth=True,
            resource_selection_mode="required",
            resource_kinds=["channel"],
        )

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str | None:
        s = _settings()
        if not s.slack_client_id.strip() or not s.slack_client_secret.strip():
            return None
        params = {
            "client_id": s.slack_client_id,
            "scope": ",".join(SLACK_SCOPES),
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        s = _settings()
        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": s.slack_client_id,
                    "client_secret": s.slack_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            res.raise_for_status()
            data = res.json()
        if not data.get("ok"):
            raise ValueError(data.get("error", "Slack OAuth failed"))
        authed = data.get("authed_user") or {}
        team = data.get("team") or {}
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "provider_metadata": {
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "user_id": authed.get("id"),
            },
        }

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles connect with credentials logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        token = credentials.get("access_token", "").strip()
        if not token:
            raise ValueError("Slack access token is required")
        return {
            "access_token": token,
            "provider_metadata": {},
        }

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return list_slack_channels(credentials, cursor=cursor, query=query)

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
        channel_ids = metadata.get("channel_ids") or []
        if not channel_ids:
            result.error = "No Slack channels selected — configure access first"
            return result
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}

        try:
            for channel_id in channel_ids[:20]:
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
        listed = cls.list_discoverable_resources(
            credentials=credentials,
            metadata=metadata,
            query=query,
        )
        hits: list[AgentSearchHit] = []
        for opt in listed.resources[:15]:
            hits.append(
                agent_search_hit(
                    id=opt.id,
                    title=opt.label,
                    snippet=opt.description or opt.kind,
                    provider=cls.provider,
                    entity_type=entity_type or opt.kind,
                )
            )
        return hits
