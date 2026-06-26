"""
File: services/api/app/routers/integrations.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Redis, Pydantic, stoa_core
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.deps.client_ip import trusted_client_ip
from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_public_rate_limit, check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.integrations import sync_integration_source
from stoa_core.config import get_settings
from stoa_core.integrations.oauth_state import consume_oauth_state, create_oauth_state
from stoa_core.integrations.hubspot_webhook import hubspot_portal_matches_metadata, verify_hubspot_signature_v3
from stoa_core.integrations.registry import get_connector
from stoa_core.integrations.provider_capabilities import list_providers_for_api
from stoa_core.integrations.service import (
    create_connection,
    get_connection_scope,
    list_connection_resources,
    list_connections,
    list_sync_runs,
    oauth_redirect_uri_for,
    revoke_connection,
    update_connection_scope,
)
from stoa_core.integrations.scope import scope_configured
from stoa_core.redis.sse import read_events_since

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


class ConnectCredentialsBody(BaseModel):
    credentials: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None


class ScopePatchBody(BaseModel):
    scope: dict[str, Any] = Field(default_factory=dict)
    sync: bool = True


class CsvImportBody(BaseModel):
    """Manage CsvImportBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    title: str = Field(default="CSV import", max_length=300)
    content: str = Field(min_length=1, max_length=10 * 1024 * 1024)
    column_mapping: dict[str, str | None] | None = None


def _maybe_enqueue_sync(connection_id: str, org_id: str, provider: str, metadata: dict[str, Any]) -> None:
    if scope_configured(provider, metadata):
        sync_integration_source.delay(connection_id, org_id, full_backfill=True)


@router.get("/providers")
def get_providers(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles get providers logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    return {"providers": list_providers_for_api()}


@router.get("/sources")
def get_sources(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles get sources logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    return {"connections": list_connections(scope.org_id)}


@router.get("/connect/{provider}")
def start_oauth(
    provider: str,
    scope: OrgScope = Depends(require_onboarded_scope),
    subdomain: str | None = Query(None),
    environment: str | None = Query(None),
    property_id: str | None = Query(None),
) -> dict[str, str]:
    """Handles start oauth logic for the surrounding Stoa workflow.

    Args:
        provider (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.
        subdomain (str | None): Zendesk subdomain for OAuth.
        environment (str | None): Salesforce environment (production | sandbox).
        property_id (str | None): GA4 property ID to store on the connection.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    connector = get_connector(provider)
    info = connector.provider_info()
    if info.auth_type != "oauth" and not info.supports_credential_auth:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provider does not use OAuth")
    redirect_uri = oauth_redirect_uri_for(provider)
    oauth_extra: dict[str, Any] = {}
    oauth_params: dict[str, Any] = {}
    if subdomain:
        oauth_extra["subdomain"] = subdomain.strip()
        oauth_params["subdomain"] = subdomain.strip()
    if environment:
        oauth_extra["environment"] = environment.strip()
        oauth_params["environment"] = environment.strip()
    if property_id:
        oauth_extra["property_id"] = property_id.strip()
        oauth_params["property_id"] = property_id.strip()
    state = create_oauth_state(scope.org_id, scope.user_id, provider, extra=oauth_extra or None)
    url = connector.oauth_authorize_url(state, redirect_uri, oauth_params=oauth_params or None)
    if not url:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "OAuth not configured for provider")
    return {"authorize_url": url}


@router.get("/callback/{provider}")
def oauth_callback(
    provider: str,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> RedirectResponse:
    """Handles oauth callback logic for the surrounding Stoa workflow.

    Args:
        provider (str): Input value used by this workflow step.
        code (str | None): OAuth authorization code.
        state (str | None): OAuth state token.
        error (str | None): OAuth error code from provider.
        error_description (str | None): Human-readable OAuth error.

    Returns:
        RedirectResponse: Result produced for the caller.
    """
    app_url = get_settings().app_base_url.rstrip("/")
    integrations_url = f"{app_url}/data/integrations"

    if error:
        from urllib.parse import quote

        msg = error_description or error
        return RedirectResponse(f"{integrations_url}?error={quote(msg)}&provider={provider}")

    if not code or not state:
        return RedirectResponse(f"{integrations_url}?error=missing_oauth_params&provider={provider}")

    oauth_state = consume_oauth_state(state)
    if not oauth_state or oauth_state.get("provider") != provider:
        return RedirectResponse(f"{integrations_url}?error=invalid_oauth_state&provider={provider}")

    try:
        org_id = oauth_state["org_id"]
        user_id = oauth_state.get("user_id")
        connector = get_connector(provider)
        redirect_uri = oauth_redirect_uri_for(provider)
        oauth_context = {
            k: oauth_state[k]
            for k in ("subdomain", "environment", "property_id")
            if oauth_state.get(k)
        }
        token_data = connector.exchange_oauth_code(code, redirect_uri, oauth_context=oauth_context or None)
        credentials = {k: v for k, v in token_data.items() if k != "provider_metadata"}
        metadata = token_data.get("provider_metadata") or {}
        for key in ("subdomain", "environment", "property_id"):
            if oauth_state.get(key):
                metadata[key] = oauth_state[key]
        info = connector.provider_info()
        conn = create_connection(
            org_id,
            provider,
            user_id=user_id,
            label=info.name,
            credentials=credentials,
            provider_metadata=metadata,
            scopes=info.scopes,
        )
        write_audit(org_id, user_id or "", "integration.connected", "integration_connection", conn["id"])
        _maybe_enqueue_sync(conn["id"], org_id, provider, metadata)
        needs_scope = not scope_configured(provider, metadata)
        return RedirectResponse(
            f"{integrations_url}?connected={provider}&connection_id={conn['id']}"
            + ("&configure_scope=1" if needs_scope else "")
        )
    except Exception as exc:
        from urllib.parse import quote

        return RedirectResponse(
            f"{integrations_url}?error={quote(str(exc))}&provider={provider}"
        )


@router.post("/sources/{provider}/connect")
def connect_with_credentials(
    provider: str,
    body: ConnectCredentialsBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles connect with credentials logic for the surrounding Stoa workflow.

    Args:
        provider (str): Input value used by this workflow step.
        body (ConnectCredentialsBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    connector = get_connector(provider)
    info = connector.provider_info()
    normalized = connector.connect_with_credentials(body.credentials)
    metadata = normalized.pop("provider_metadata", {})
    label = body.label or info.name
    conn = create_connection(
        scope.org_id,
        provider,
        user_id=scope.user_id,
        label=label,
        credentials=normalized,
        provider_metadata=metadata,
    )
    write_audit(scope.org_id, scope.user_id, "integration.connected", "integration_connection", conn["id"])
    _maybe_enqueue_sync(conn["id"], scope.org_id, provider, metadata)
    return {"connection": conn, "needs_scope_configuration": not scope_configured(provider, metadata)}


@router.post("/sources/{connection_id}/sync")
def trigger_sync(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
    full: bool = Query(False),
) -> dict[str, Any]:
    """Handles trigger sync logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.
        full (bool): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    sync_integration_source.delay(connection_id, scope.org_id, full_backfill=full)
    return {"status": "queued", "connection_id": connection_id}


@router.delete("/sources/{connection_id}")
def disconnect(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, str]:
    """Handles disconnect logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:write")
    revoke_connection(connection_id, scope.org_id)
    write_audit(scope.org_id, scope.user_id, "integration.revoked", "integration_connection", connection_id)
    return {"status": "revoked"}


@router.get("/sources/{connection_id}/scope")
def get_scope(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    try:
        return get_connection_scope(connection_id, scope.org_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/sources/{connection_id}/resources")
def list_resources(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
    cursor: str | None = Query(None),
    q: str | None = Query(None),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integration_resources")
    try:
        return list_connection_resources(connection_id, scope.org_id, cursor=cursor, query=q)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.patch("/sources/{connection_id}/scope")
def patch_scope(
    connection_id: str,
    body: ScopePatchBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    patch = dict(body.scope)
    patch["scope_configured"] = True
    try:
        conn = update_connection_scope(connection_id, scope.org_id, patch)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    write_audit(scope.org_id, scope.user_id, "integration.scope_updated", "integration_connection", connection_id)
    if body.sync and conn:
        meta = conn.get("provider_metadata") or {}
        _maybe_enqueue_sync(connection_id, scope.org_id, conn.get("provider", ""), meta)
    return {"connection": conn}


@router.get("/sources/{connection_id}/runs")
def get_sync_runs(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles get sync runs logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    return {"runs": list_sync_runs(connection_id, scope.org_id)}


@router.post("/csv/detect")
def detect_csv_columns(
    body: CsvImportBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles detect csv columns logic for the surrounding Stoa workflow.

    Args:
        body (CsvImportBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    from stoa_core.integrations.csv_structured import CSV_FIELD_DEFINITIONS, parse_csv_content

    headers, mapping = parse_csv_content(body.content)
    return {
        "headers": headers,
        "suggested_mapping": mapping,
        "fields": CSV_FIELD_DEFINITIONS,
    }


@router.post("/csv/import")
def import_structured_csv(
    body: CsvImportBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles import structured csv logic for the surrounding Stoa workflow.

    Args:
        body (CsvImportBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    from stoa_core.integrations.csv_structured import detect_columns

    from app.services.document_ingestion import queue_text_document

    mapping = body.column_mapping or detect_columns(
        __import__("csv").DictReader(__import__("io").StringIO(body.content)).fieldnames or []
    )
    try:
        doc, _job = queue_text_document(
            org_id=scope.org_id,
            user_id=scope.user_id,
            title=body.title,
            content=body.content,
            doc_type="crm_export",
            feature_origin="integrations",
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    conn = create_connection(
        scope.org_id,
        "csv_structured",
        user_id=scope.user_id,
        label=body.title,
        credentials={
            "csv_content": body.content,
            "column_mapping": mapping,
        },
        provider_metadata={"document_id": doc["id"] if doc else None},
    )
    write_audit(scope.org_id, scope.user_id, "integration.csv_import", "integration_connection", conn["id"])
    if doc:
        write_audit(scope.org_id, scope.user_id, "document.csv_imported", "document", doc["id"])
    sync_integration_source.delay(conn["id"], scope.org_id, full_backfill=True)
    return {"connection": conn, "document": doc, "column_mapping": mapping}


@router.get("/sources/{connection_id}/events")
async def integration_events(
    connection_id: str,
    request: Request,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> StreamingResponse:
    """Asynchronously handles integration events logic for the surrounding Stoa workflow.

    Args:
        connection_id (str): Input value used by this workflow step.
        request (Request): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        StreamingResponse: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    from stoa_core.db.supabase import get_supabase_admin

    sb = get_supabase_admin()
    conn = (
        sb.table("integration_connections")
        .select("id")
        .eq("id", connection_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not conn.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection not found")

    async def _gen():
        """Asynchronously handles  gen logic for the surrounding Stoa workflow.

        Returns:
            Any: Result produced for the caller.
        """
        last_id = request.headers.get("Last-Event-ID", "0-0")
        async for msg_id, data in read_events_since("integration", connection_id, last_id):
            yield f"id: {msg_id}\ndata: {__import__('json').dumps(data)}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.post("/webhooks/hubspot")
async def hubspot_webhook(request: Request) -> dict[str, str | int]:
    """HubSpot webhook receiver — queues sync for matching portal."""
    from stoa_core.db.supabase import get_supabase_admin

    check_public_rate_limit(trusted_client_ip(request), scope="hubspot_webhook", ip_limit_per_minute=120)

    settings = get_settings()
    body = await request.body()
    secret = settings.hubspot_client_secret.strip()
    # In local development only, allow unsigned webhooks when the client secret is unset.
    if secret:
        signature = request.headers.get("X-HubSpot-Signature-v3")
        timestamp = request.headers.get("X-HubSpot-Request-Timestamp")
        request_uri = str(request.url.path)
        if request.url.query:
            request_uri = f"{request_uri}?{request.url.query}"
        if not verify_hubspot_signature_v3(
            client_secret=secret,
            method=request.method,
            request_uri=request_uri,
            body=body,
            signature=signature,
            timestamp=timestamp,
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid HubSpot webhook signature")
    elif not settings.is_development:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "HubSpot webhook signature required")

    try:
        import json

        payload = json.loads(body.decode("utf-8") if body else "null")
    except Exception:
        return {"status": "ignored"}

    events = payload if isinstance(payload, list) else [payload]
    portal_id = None
    for ev in events:
        if isinstance(ev, dict) and ev.get("portalId"):
            portal_id = str(ev["portalId"])
            break

    if not portal_id:
        return {"status": "ignored"}

    sb = get_supabase_admin()
    res = (
        sb.table("integration_connections")
        .select("id, org_id, provider_metadata")
        .eq("provider", "hubspot")
        .eq("status", "active")
        .execute()
    )
    matched = [
        row
        for row in (res.data or [])
        if hubspot_portal_matches_metadata(portal_id, row.get("provider_metadata"))
    ]
    for row in matched:
        sync_integration_source.delay(row["id"], row["org_id"])
    return {"status": "queued", "count": len(matched)}
