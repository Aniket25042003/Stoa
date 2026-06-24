"""
File: services/core/src/stoa_core/integrations/service.py
Layer: Core Integration Connectors
Purpose: Implements service behavior for the core integration connectors.
Dependencies: Supabase, Redis, stoa_core
"""


from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.integrations.crypto import decrypt_credentials, encrypt_credentials
from stoa_core.integrations.registry import get_connector
from stoa_core.redis.client import publish_event
from stoa_core.security.client_errors import client_safe_error_message

logger = logging.getLogger(__name__)


def connection_for_client(conn: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip secrets and sanitize errors before returning to API clients."""
    if not conn:
        return None
    safe = {k: v for k, v in conn.items() if k != "credentials_encrypted"}
    if safe.get("last_error"):
        safe["last_error"] = client_safe_error_message(str(safe["last_error"]), context="sync")
    return safe


def _client_safe_sync_error(error: str | None) -> str | None:
    return client_safe_error_message(error, context="sync")


def _publish_integration_event(connection_id: str, payload: dict[str, Any]) -> None:
    safe = dict(payload)
    if "error" in safe and safe["error"]:
        safe["error"] = _client_safe_sync_error(str(safe["error"]))
    publish_event("integration", connection_id, safe)


def oauth_redirect_uri_for(provider: str) -> str:
    """Handles oauth redirect uri for logic for the surrounding Stoa workflow.

    Args:
        provider (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    from stoa_core.config import get_settings

    base = get_settings().api_base_url.rstrip("/")
    return f"{base}/v1/integrations/callback/{provider}"


def create_connection(
    org_id: str,
    provider: str,
    *,
    user_id: str | None,
    label: str,
    credentials: dict[str, Any],
    provider_metadata: dict[str, Any] | None = None,
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Handles create connection logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        provider (str): Input value used by this workflow step.
        user_id (str | None): Input value used by this workflow step.
        label (str): Input value used by this workflow step.
        credentials (dict[str, Any]): Input value used by this workflow step.
        provider_metadata (dict[str, Any] | None): Input value used by this workflow step.
        scopes (list[str] | None): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    sb = get_supabase_admin()

    existing = (
        sb.table("integration_connections")
        .select("id, data_source_id")
        .eq("org_id", org_id)
        .eq("provider", provider)
        .limit(1)
        .execute()
    )
    existing_row = (existing.data or [None])[0]

    if existing_row:
        sb.table("integration_connections").update(
            {
                "status": "active",
                "label": label,
                "credentials_encrypted": encrypt_credentials(credentials),
                "provider_metadata": provider_metadata or {},
                "scopes": scopes or [],
                "last_error": None,
                "sync_cursor": {},
            }
        ).eq("id", existing_row["id"]).execute()
        res = (
            sb.table("integration_connections")
            .select("*")
            .eq("id", existing_row["id"])
            .limit(1)
            .execute()
        )
        return connection_for_client((res.data or [None])[0])

    ds_res = (
        sb.table("data_sources")
        .insert(
            {
                "org_id": org_id,
                "source_type": provider,
                "label": label,
                "status": "active",
                "metadata": {"provider": provider},
            }
        )
        .execute()
    )
    data_source = (ds_res.data or [None])[0]

    conn_res = (
        sb.table("integration_connections")
        .insert(
            {
                "org_id": org_id,
                "provider": provider,
                "status": "active",
                "label": label,
                "credentials_encrypted": encrypt_credentials(credentials),
                "provider_metadata": provider_metadata or {},
                "scopes": scopes or [],
                "data_source_id": data_source["id"] if data_source else None,
                "created_by": user_id,
            }
        )
        .execute()
    )
    return connection_for_client((conn_res.data or [None])[0])


def get_connection(connection_id: str, org_id: str) -> dict[str, Any] | None:
    """Handles get connection logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("integration_connections")
        .select("*")
        .eq("id", connection_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def list_connections(org_id: str) -> list[dict[str, Any]]:
    """Handles list connections logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("integration_connections")
        .select("id, org_id, provider, status, label, last_sync_at, last_error, provider_metadata, created_at, data_source_id")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = res.data or []
    for row in rows:
        if row.get("last_error"):
            row["last_error"] = client_safe_error_message(str(row["last_error"]), context="sync")
    return rows


def revoke_connection(connection_id: str, org_id: str) -> None:
    """Handles revoke connection logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    sb.table("integration_connections").update(
        {"status": "revoked", "credentials_encrypted": None}
    ).eq("id", connection_id).eq("org_id", org_id).execute()


def run_sync(connection_id: str, org_id: str, *, full_backfill: bool = False) -> dict[str, Any]:
    """Handles run sync logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.
        full_backfill (bool): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    conn = get_connection(connection_id, org_id)
    if not conn:
        raise ValueError("Connection not found")
    if conn.get("status") == "revoked":
        raise ValueError("Connection is revoked")

    run_res = (
        sb.table("integration_sync_runs")
        .insert(
            {
                "org_id": org_id,
                "connection_id": connection_id,
                "status": "running",
                "started_at": datetime.now(UTC).isoformat(),
            }
        )
        .execute()
    )
    sync_run = (run_res.data or [None])[0]
    run_id = sync_run["id"] if sync_run else connection_id

    publish_event("integration", connection_id, {"status": "running", "run_id": run_id})

    credentials = decrypt_credentials(conn.get("credentials_encrypted"))
    cursor = conn.get("sync_cursor") or {}
    connector = get_connector(conn["provider"])

    try:
        result = connector.sync(
            org_id,
            conn,
            credentials=credentials,
            cursor=cursor if not full_backfill else {},
            full_backfill=full_backfill,
        )

        update_payload: dict[str, Any] = {
            "last_sync_at": datetime.now(UTC).isoformat(),
            "sync_cursor": result.cursor,
            "status": "error" if result.error else "active",
            "last_error": result.error,
        }
        if credentials != decrypt_credentials(conn.get("credentials_encrypted")):
            update_payload["credentials_encrypted"] = encrypt_credentials(credentials)

        sb.table("integration_connections").update(update_payload).eq("id", connection_id).execute()

        sb.table("integration_sync_runs").update(
            {
                "status": "failed" if result.error else "completed",
                "records_fetched": result.records_fetched,
                "records_written": result.records_written,
                "error": result.error,
                "finished_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", run_id).execute()

        _publish_integration_event(
            connection_id,
            {
                "status": "failed" if result.error else "completed",
                "run_id": run_id,
                "records_written": result.records_written,
                "error": result.error,
            },
        )

        return {
            "run_id": run_id,
            "records_fetched": result.records_fetched,
            "records_written": result.records_written,
            "error": result.error,
        }

    except Exception as exc:
        logger.exception("Sync failed for connection %s", connection_id)
        sb.table("integration_sync_runs").update(
            {
                "status": "failed",
                "error": str(exc),
                "finished_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", run_id).execute()
        sb.table("integration_connections").update(
            {"status": "error", "last_error": str(exc)}
        ).eq("id", connection_id).execute()
        _publish_integration_event(connection_id, {"status": "failed", "error": str(exc)})
        raise


def list_sync_runs(connection_id: str, org_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Handles list sync runs logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.
        limit (int): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    conn = get_connection(connection_id, org_id)
    if not conn:
        return []
    res = (
        sb.table("integration_sync_runs")
        .select("id, status, records_fetched, records_written, error, started_at, finished_at, created_at")
        .eq("connection_id", connection_id)
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    for row in rows:
        if row.get("error"):
            row["error"] = client_safe_error_message(str(row["error"]), context="sync")
    return rows
