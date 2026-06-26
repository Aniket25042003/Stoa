"""
File: services/core/src/stoa_core/integrations/google_drive.py
Layer: Core Integration Connectors
Purpose: Implements google drive behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.google_oauth import (
    DRIVE_SCOPE,
    exchange_google_code,
    google_authorize_url,
    google_oauth_configured,
)
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_google_drive_files
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

SOURCE = "google_drive"


@register_connector
class GoogleDriveConnector(BaseConnector):
    """Manage GoogleDriveConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "google_drive"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="google_drive",
            name="Google Drive",
            auth_type="oauth",
            description="Export Google Docs as text into the knowledge base.",
            scopes=[DRIVE_SCOPE],
            supports_credential_auth=True,
            resource_selection_mode="required",
            resource_kinds=["file"],
        )

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str | None:
        if not google_oauth_configured():
            return None
        return google_authorize_url(state, redirect_uri, [DRIVE_SCOPE])

    @classmethod
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return exchange_google_code(code, redirect_uri)

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
            raise ValueError("Google Drive access token is required")
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
        return list_google_drive_files(credentials, cursor=cursor, query=query)

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
        file_ids = metadata.get("file_ids") or []
        if not file_ids:
            result.error = "No Google Drive files selected — configure access first"
            return result
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}

        try:
            for file_id in file_ids[:20]:
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
