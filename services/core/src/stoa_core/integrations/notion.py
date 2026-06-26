"""
File: services/core/src/stoa_core/integrations/notion.py
Layer: Core Integration Connectors
Purpose: Implements notion behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_notion_resources
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "notion"


@register_connector
class NotionConnector(BaseConnector):
    """Manage NotionConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "notion"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="notion",
            name="Notion",
            auth_type="api_key",
            description="Import Notion pages into the knowledge base.",
            resource_selection_mode="required",
            resource_kinds=["page", "database"],
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
            raise ValueError("Notion integration token is required")
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
        return list_notion_resources(credentials, cursor=cursor, query=query)

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
        page_ids = metadata.get("page_ids") or []
        database_ids = metadata.get("database_ids") or []
        if not page_ids and not database_ids:
            result.error = "No Notion pages or databases selected — configure access first"
            return result
        headers = {
            "Authorization": f"Bearer {credentials['access_token']}",
            "Notion-Version": "2022-06-28",
        }

        try:
            for page_id in page_ids[:20]:
                text = cls._fetch_page_text(page_id, headers)
                if not text.strip():
                    continue
                result.records_fetched += 1
                ingest_knowledge(
                    org_id,
                    kind="document",
                    title=f"Notion page {page_id[:8]}",
                    text=text,
                    feature_origin="integrations",
                    uri=f"notion:page:{page_id}",
                    metadata={"source": SOURCE},
                )
                result.records_written += 1
            for db_id in database_ids[:10]:
                rows = cls._query_database(db_id, headers)
                if not rows.strip():
                    continue
                result.records_fetched += 1
                ingest_knowledge(
                    org_id,
                    kind="document",
                    title=f"Notion database {db_id[:8]}",
                    text=rows,
                    feature_origin="integrations",
                    uri=f"notion:database:{db_id}",
                    metadata={"source": SOURCE},
                )
                result.records_written += 1
            result.cursor = {"stage": "done"}
        except Exception as exc:
            logger.exception("Notion sync failed for org %s", org_id)
            result.error = str(exc)
        return result

    @classmethod
    def _fetch_page_text(cls, page_id: str, headers: dict[str, str]) -> str:
        """Handles  fetch page text logic for the surrounding Stoa workflow.

        Args:
            page_id (str): Input value used by this workflow step.
            headers (dict[str, str]): Input value used by this workflow step.

        Returns:
            str: Result produced for the caller.
        """
        lines: list[str] = []
        start_cursor = None
        with httpx.Client(timeout=60) as client:
            while True:
                params: dict[str, Any] = {"page_size": 100}
                if start_cursor:
                    params["start_cursor"] = start_cursor
                res = client.get(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers,
                    params=params,
                )
                if res.status_code >= 400:
                    break
                body = res.json()
                for block in body.get("results") or []:
                    text = _block_text(block)
                    if text:
                        lines.append(text)
                if not body.get("has_more"):
                    break
                start_cursor = body.get("next_cursor")
        return "\n".join(lines)

    @classmethod
    def _query_database(cls, database_id: str, headers: dict[str, str]) -> str:
        lines: list[str] = []
        start_cursor = None
        with httpx.Client(timeout=60) as client:
            while len(lines) < 200:
                payload: dict[str, Any] = {"page_size": 50}
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                res = client.post(
                    f"https://api.notion.com/v1/databases/{database_id}/query",
                    headers=headers,
                    json=payload,
                )
                if res.status_code >= 400:
                    break
                body = res.json()
                for page in body.get("results") or []:
                    for prop in (page.get("properties") or {}).values():
                        if prop.get("type") == "title":
                            title_bits = prop.get("title") or []
                            lines.append("".join(t.get("plain_text", "") for t in title_bits))
                if not body.get("has_more"):
                    break
                start_cursor = body.get("next_cursor")
        return "\n".join(lines)


def _block_text(block: dict[str, Any]) -> str:
    """Handles  block text logic for the surrounding Stoa workflow.

    Args:
        block (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    btype = block.get("type")
    if not btype:
        return ""
    rich = (block.get(btype) or {}).get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in rich)
