"""Google Drive documents connector (KB enrichment)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "google_drive"


@register_connector
class GoogleDriveConnector(BaseConnector):
    provider = "google_drive"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="google_drive",
            name="Google Drive",
            auth_type="oauth",
            description="Export Google Docs as text into the knowledge base.",
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        token = credentials.get("access_token", "").strip()
        file_ids = credentials.get("file_ids") or []
        if not token:
            raise ValueError("Google Drive access token is required")
        return {
            "access_token": token,
            "provider_metadata": {"file_ids": file_ids},
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
        file_ids = metadata.get("file_ids") or []
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}

        try:
            for file_id in file_ids[:10]:
                with httpx.Client(timeout=60) as client:
                    res = client.get(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                        headers=headers,
                        params={"mimeType": "text/plain"},
                    )
                    if res.status_code >= 400:
                        continue
                    text = res.text
                result.records_fetched += 1
                ingest_knowledge(
                    org_id,
                    kind="document",
                    title=f"Google Drive file {file_id[:8]}",
                    text=text,
                    feature_origin="integrations",
                    uri=f"google_drive:file:{file_id}",
                    metadata={"source": SOURCE},
                )
                result.records_written += 1
            result.cursor = {"stage": "done"}
        except Exception as exc:
            logger.exception("Google Drive sync failed for org %s", org_id)
            result.error = str(exc)
        return result
