"""Zendesk support ticket connector."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "zendesk"


@register_connector
class ZendeskConnector(BaseConnector):
    provider = "zendesk"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="zendesk",
            name="Zendesk",
            auth_type="oauth",
            description="Sync support tickets and conversation threads from Zendesk.",
            scopes=["read"],
        )

    @classmethod
    def oauth_authorize_url(cls, state: str, redirect_uri: str) -> str:
        s = get_settings()
        subdomain = s.zendesk_subdomain or "subdomain"
        params = {
            "response_type": "code",
            "client_id": s.zendesk_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read",
            "state": state,
        }
        return f"https://{subdomain}.zendesk.com/oauth/authorizations/new?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        s = get_settings()
        subdomain = s.zendesk_subdomain
        if not subdomain:
            raise ValueError("ZENDESK_SUBDOMAIN is required")
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
        result = SyncResult(cursor=dict(cursor))
        metadata = connection.get("provider_metadata") or {}
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
