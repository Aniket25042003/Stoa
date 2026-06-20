"""
File: services/core/src/stoa_core/integrations/intercom.py
Layer: Core Integration Connectors
Purpose: Implements intercom behavior for the core integration connectors.
Dependencies: Next.js, stoa_core
"""


from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_contact, upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "intercom"
BASE_URL = "https://api.intercom.io"


@register_connector
class IntercomConnector(BaseConnector):
    """Manage IntercomConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "intercom"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="intercom",
            name="Intercom",
            auth_type="api_key",
            description="Sync conversations and contacts from Intercom.",
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
        if not token:
            raise ValueError("Intercom access token is required")
        region = credentials.get("region", "us").strip().lower()
        base_url = BASE_URL
        if region == "eu":
            base_url = "https://api.eu.intercom.io"
        elif region == "au":
            base_url = "https://api.au.intercom.io"
        return {
            "access_token": token,
            "provider_metadata": {"base_url": base_url},
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
        result = SyncResult(cursor=dict(cursor))
        metadata = connection.get("provider_metadata") or {}
        base_url = metadata.get("base_url", BASE_URL)
        headers = {
            "Authorization": f"Bearer {credentials['access_token']}",
            "Accept": "application/json",
            "Intercom-Version": "2.11",
        }
        starting_after = cursor.get("starting_after")

        try:
            params: dict[str, Any] = {"per_page": 20}
            if starting_after:
                params["starting_after"] = starting_after

            with httpx.Client(timeout=60) as client:
                conv_res = client.get(f"{base_url}/conversations", headers=headers, params=params)
                conv_res.raise_for_status()
                conv_body = conv_res.json()

            conversations = conv_body.get("conversations") or conv_body.get("data") or []
            result.records_fetched += len(conversations)

            for conv in conversations[:20]:
                conv_id = str(conv.get("id"))
                title = conv.get("title") or f"Conversation {conv_id}"
                body_text = cls._conversation_text(conv)
                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": conv_id,
                        "interaction_type": "support_ticket",
                        "occurred_at": _ts(conv.get("created_at")),
                        "title": title,
                        "body_text": body_text,
                        "raw_properties": conv,
                    },
                )
                if saved:
                    result.records_written += 1
                time.sleep(0.15)

            pages = conv_body.get("pages") or {}
            next_start = pages.get("next", {}).get("starting_after")
            if next_start:
                result.cursor = {"starting_after": next_start}
            else:
                result.cursor = {"stage": "done"}

            if cursor.get("stage") != "contacts_done":
                cls._sync_contacts(org_id, base_url, headers, result)

        except Exception as exc:
            logger.exception("Intercom sync failed for org %s", org_id)
            result.error = str(exc)

        return result

    @classmethod
    def _sync_contacts(cls, org_id: str, base_url: str, headers: dict[str, str], result: SyncResult) -> None:
        """Handles  sync contacts logic for the surrounding Stoa workflow.

        Args:
            org_id (str): Input value used by this workflow step.
            base_url (str): Input value used by this workflow step.
            headers (dict[str, str]): Input value used by this workflow step.
            result (SyncResult): Input value used by this workflow step.
        """
        with httpx.Client(timeout=60) as client:
            res = client.get(f"{base_url}/contacts", headers=headers, params={"per_page": 50})
            if res.status_code >= 400:
                return
            for contact in res.json().get("data") or []:
                ext_id = str(contact.get("id"))
                saved = upsert_contact(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": ext_id,
                        "email": contact.get("email"),
                        "name": contact.get("name"),
                        "raw_properties": contact,
                    },
                )
                if saved:
                    result.records_written += 1

    @classmethod
    def _conversation_text(cls, conv: dict[str, Any]) -> str:
        """Handles  conversation text logic for the surrounding Stoa workflow.

        Args:
            conv (dict[str, Any]): Input value used by this workflow step.

        Returns:
            str: Result produced for the caller.
        """
        parts = [conv.get("source", {}).get("body") or ""]
        for part in conv.get("conversation_parts", {}).get("conversation_parts") or []:
            parts.append(part.get("body") or "")
        return "\n".join(p for p in parts if p)


def _ts(value: Any) -> str | None:
    """Handles  ts logic for the surrounding Stoa workflow.

    Args:
        value (Any): Input value used by this workflow step.

    Returns:
        str | None: Result produced for the caller.
    """
    if value is None:
        return None
    return str(value)
