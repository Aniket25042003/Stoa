"""Notion pages connector (KB enrichment)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "notion"


@register_connector
class NotionConnector(BaseConnector):
    provider = "notion"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="notion",
            name="Notion",
            auth_type="api_key",
            description="Import Notion pages into the knowledge base.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        token = credentials.get("access_token", "").strip()
        page_ids = credentials.get("page_ids") or []
        if not token:
            raise ValueError("Notion integration token is required")
        return {
            "access_token": token,
            "provider_metadata": {"page_ids": page_ids},
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
        page_ids = metadata.get("page_ids") or []
        headers = {
            "Authorization": f"Bearer {credentials['access_token']}",
            "Notion-Version": "2022-06-28",
        }

        try:
            for page_id in page_ids[:10]:
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
            result.cursor = {"stage": "done"}
        except Exception as exc:
            logger.exception("Notion sync failed for org %s", org_id)
            result.error = str(exc)
        return result

    @classmethod
    def _fetch_page_text(cls, page_id: str, headers: dict[str, str]) -> str:
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


def _block_text(block: dict[str, Any]) -> str:
    btype = block.get("type")
    if not btype:
        return ""
    rich = (block.get(btype) or {}).get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in rich)
