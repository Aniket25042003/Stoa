"""
File: services/core/src/stoa_core/integrations/zendesk.py
Layer: Core Integration Connectors
Purpose: Implements zendesk behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_zendesk_views
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "zendesk"


@register_connector
class ZendeskConnector(BaseConnector):
    """Manage ZendeskConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "zendesk"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="zendesk",
            name="Zendesk",
            auth_type="oauth",
            description="Sync support tickets and conversation threads from Zendesk.",
            scopes=["read"],
            supports_credential_auth=True,
            resource_selection_mode="required",
            resource_kinds=["view"],
        )

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return list_zendesk_views(credentials, metadata)

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str | None:
        s = get_settings()
        oauth_params = oauth_params or {}
        subdomain = (oauth_params.get("subdomain") or s.zendesk_subdomain or "").strip()
        if not subdomain or not s.zendesk_client_id.strip():
            return None
        params = {
            "response_type": "code",
            "client_id": s.zendesk_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read",
            "state": state,
        }
        return f"https://{subdomain}.zendesk.com/oauth/authorizations/new?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handles exchange oauth code logic for the surrounding Stoa workflow.

        Args:
            code (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.
            oauth_context (dict[str, Any] | None): Values from OAuth state (subdomain, etc.).

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        s = get_settings()
        oauth_context = oauth_context or {}
        subdomain = (oauth_context.get("subdomain") or s.zendesk_subdomain or "").strip()
        if not subdomain:
            raise ValueError("Zendesk subdomain is required")
        with httpx.Client(timeout=30) as client:
            res = client.post(
                f"https://{subdomain}.zendesk.com/oauth/tokens",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": s.zendesk_client_id,
                    "client_secret": s.zendesk_client_secret,
                    "redirect_uri": redirect_uri,
                    "scope": "read",
                },
            )
            res.raise_for_status()
            data = res.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "provider_metadata": {"subdomain": subdomain},
        }

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles connect with credentials logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        subdomain = credentials.get("subdomain", "").strip()
        email = credentials.get("email", "").strip()
        api_token = credentials.get("api_token", "").strip()
        if not subdomain or not email or not api_token:
            raise ValueError("Zendesk subdomain, email, and api_token are required")
        return {
            "subdomain": subdomain,
            "email": email,
            "api_token": api_token,
            "provider_metadata": {"subdomain": subdomain, "auth_mode": "token"},
        }

    @classmethod
    def _auth(cls, credentials: dict[str, Any], metadata: dict[str, Any]) -> tuple[str, Any]:
        """Handles  auth logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.
            metadata (dict[str, Any]): Input value used by this workflow step.

        Returns:
            tuple[str, Any]: Result produced for the caller.
        """
        subdomain = metadata.get("subdomain") or credentials.get("subdomain")
        base = f"https://{subdomain}.zendesk.com/api/v2"
        if credentials.get("api_token"):
            return base, httpx.BasicAuth(f"{credentials['email']}/token", credentials["api_token"])
        return base, {"Authorization": f"Bearer {credentials['access_token']}"}

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
        result = SyncResult(cursor=dict(cursor))
        metadata = connection.get("provider_metadata") or {}
        view_ids = metadata.get("view_ids") or []
        sync_all = metadata.get("sync_all_tickets")
        if not sync_all and not view_ids:
            result.error = "No Zendesk views selected — configure access first"
            return result
        if view_ids and not sync_all:
            return cls._sync_views(org_id, credentials, metadata, view_ids, result)
        base, auth = cls._auth(credentials, metadata)
        start_time = cursor.get("start_time", 0)
        page_url = cursor.get("next_page") or f"{base}/incremental/tickets.json?start_time={start_time}"

        try:
            with httpx.Client(timeout=60) as client:
                res = client.get(
                    page_url,
                    auth=auth if isinstance(auth, httpx.BasicAuth) else None,
                    headers=auth if isinstance(auth, dict) else None,
                )
                res.raise_for_status()
                body = res.json()

            tickets = body.get("tickets") or []
            result.records_fetched += len(tickets)

            for ticket in tickets[:30]:
                ticket_id = str(ticket.get("id"))
                comments_text = cls._fetch_comments(base, auth, ticket_id)
                body_text = f"Subject: {ticket.get('subject', '')}\n\n{comments_text}"
                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": ticket_id,
                        "interaction_type": "support_ticket",
                        "occurred_at": ticket.get("created_at"),
                        "title": ticket.get("subject") or f"Ticket {ticket_id}",
                        "body_text": body_text,
                        "raw_properties": ticket,
                    },
                )
                if saved:
                    result.records_written += 1
                time.sleep(0.2)

            end_time = body.get("end_time")
            next_page = body.get("next_page")
            if next_page:
                result.cursor = {"next_page": next_page}
            elif end_time:
                result.cursor = {"start_time": end_time, "stage": "done"}
            else:
                result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("Zendesk sync failed for org %s", org_id)
            result.error = str(exc)

        return result

    @classmethod
    def _fetch_comments(cls, base: str, auth: Any, ticket_id: str) -> str:
        """Handles  fetch comments logic for the surrounding Stoa workflow.

        Args:
            base (str): Input value used by this workflow step.
            auth (Any): Input value used by this workflow step.
            ticket_id (str): Input value used by this workflow step.

        Returns:
            str: Result produced for the caller.
        """
        lines: list[str] = []
        url = f"{base}/tickets/{ticket_id}/comments.json"
        with httpx.Client(timeout=30) as client:
            res = client.get(
                url,
                auth=auth if isinstance(auth, httpx.BasicAuth) else None,
                headers=auth if isinstance(auth, dict) else None,
            )
            if res.status_code >= 400:
                return ""
            for comment in res.json().get("comments") or []:
                body = comment.get("body") or ""
                author = comment.get("author_id")
                lines.append(f"[{author}]: {body}")
        return "\n".join(lines)

    @classmethod
    def _sync_views(
        cls,
        org_id: str,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        view_ids: list[str],
        result: SyncResult,
    ) -> SyncResult:
        base, auth = cls._auth(credentials, metadata)
        try:
            for view_id in view_ids[:10]:
                if view_id == "__all__":
                    continue
                url = f"{base}/views/{view_id}/tickets.json"
                with httpx.Client(timeout=60) as client:
                    res = client.get(
                        url,
                        auth=auth if isinstance(auth, httpx.BasicAuth) else None,
                        headers=auth if isinstance(auth, dict) else None,
                    )
                    if res.status_code >= 400:
                        continue
                    tickets = res.json().get("tickets") or []
                result.records_fetched += len(tickets)
                for ticket in tickets[:30]:
                    ticket_id = str(ticket.get("id"))
                    comments_text = cls._fetch_comments(base, auth, ticket_id)
                    body_text = f"Subject: {ticket.get('subject', '')}\n\n{comments_text}"
                    saved = upsert_interaction(
                        org_id,
                        {
                            "external_source": SOURCE,
                            "external_id": ticket_id,
                            "interaction_type": "support_ticket",
                            "occurred_at": ticket.get("created_at"),
                            "title": ticket.get("subject") or f"Ticket {ticket_id}",
                            "body_text": body_text,
                            "raw_properties": ticket,
                        },
                    )
                    if saved:
                        result.records_written += 1
            result.cursor = {"stage": "done"}
        except Exception as exc:
            logger.exception("Zendesk view sync failed")
            result.error = str(exc)
        return result
