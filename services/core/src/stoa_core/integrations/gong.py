"""Gong call intelligence connector."""

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

SOURCE = "gong"


@register_connector
class GongConnector(BaseConnector):
    provider = "gong"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="gong",
            name="Gong",
            auth_type="oauth",
            description="Sync call transcripts and metadata from Gong.",
            scopes=["api:calls:read:basic", "api:calls:read:transcript"],
        )

    @classmethod
    def oauth_authorize_url(cls, state: str, redirect_uri: str) -> str:
        s = get_settings()
        params = {
            "client_id": s.gong_client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"https://app.gong.io/oauth2/authorize?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        s = get_settings()
        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://app.gong.io/oauth2/generate-customer-token",
                auth=(s.gong_client_id, s.gong_client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            res.raise_for_status()
            data = res.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
            "provider_metadata": {
                "api_base_url": data.get("api_base_url_for_customer", "https://api.gong.io"),
            },
        }

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Basic auth fallback: access_key + access_key_secret."""
        access_key = credentials.get("access_key", "").strip()
        secret = credentials.get("access_key_secret", "").strip()
        if not access_key or not secret:
            raise ValueError("Gong access_key and access_key_secret are required")
        base_url = credentials.get("api_base_url", "https://api.gong.io").rstrip("/")
        return {
            "access_key": access_key,
            "access_key_secret": secret,
            "provider_metadata": {"api_base_url": base_url, "auth_mode": "basic"},
        }

    @classmethod
    def _client(cls, credentials: dict[str, Any], metadata: dict[str, Any]) -> tuple[str, dict[str, str] | httpx.BasicAuth]:
        base = metadata.get("api_base_url", "https://api.gong.io").rstrip("/")
        if credentials.get("access_key"):
            return base, httpx.BasicAuth(credentials["access_key"], credentials["access_key_secret"])
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
        base_url, auth = cls._client(credentials, metadata)
        from_datetime = cursor.get("from_datetime") or "2020-01-01T00:00:00Z"
        call_cursor = cursor.get("call_cursor")

        try:
            body: dict[str, Any] = {"filter": {"fromDateTime": from_datetime}}
            if call_cursor:
                body["cursor"] = call_cursor

            with httpx.Client(timeout=60) as client:
                calls_res = client.post(
                    f"{base_url}/v2/calls",
                    auth=auth if isinstance(auth, httpx.BasicAuth) else None,
                    headers=auth if isinstance(auth, dict) else None,
                    json=body,
                )
                calls_res.raise_for_status()
                calls_body = calls_res.json()

            calls = calls_body.get("calls") or []
            result.records_fetched += len(calls)

            for call in calls[:20]:
                call_id = str(call.get("id") or call.get("metaData", {}).get("id"))
                if not call_id:
                    continue
                transcript_text = cls._fetch_transcript(base_url, auth, call_id)
                title = call.get("title") or call.get("metaData", {}).get("title") or f"Call {call_id}"
                started = call.get("started") or call.get("metaData", {}).get("started")
                participants = call.get("parties") or call.get("metaData", {}).get("parties") or []

                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": call_id,
                        "interaction_type": "call_transcript",
                        "occurred_at": started,
                        "title": title,
                        "body_text": transcript_text or "(no transcript available)",
                        "participants": participants,
                        "raw_properties": call,
                    },
                )
                if saved:
                    result.records_written += 1
                time.sleep(0.35)

            records = calls_body.get("records") or {}
            next_cursor = records.get("cursor")
            if next_cursor:
                result.cursor = {
                    "from_datetime": from_datetime,
                    "call_cursor": next_cursor,
                }
            else:
                result.cursor = {"stage": "done", "from_datetime": from_datetime}

        except Exception as exc:
            logger.exception("Gong sync failed for org %s", org_id)
            result.error = str(exc)

        return result

    @classmethod
    def _fetch_transcript(cls, base_url: str, auth: Any, call_id: str) -> str:
        with httpx.Client(timeout=60) as client:
            res = client.post(
                f"{base_url}/v2/calls/transcript",
                auth=auth if isinstance(auth, httpx.BasicAuth) else None,
                headers=auth if isinstance(auth, dict) else None,
                json={"filter": {"callIds": [call_id]}},
            )
            if res.status_code >= 400:
                return ""
            body = res.json()
        lines: list[str] = []
        for block in body.get("callTranscripts") or []:
            for t in block.get("transcript") or []:
                speaker = t.get("speakerId") or "Speaker"
                for sentence in t.get("sentences") or []:
                    text = sentence.get("text") or ""
                    if text:
                        lines.append(f"{speaker}: {text}")
        return "\n".join(lines)
