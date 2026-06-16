from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.integrations import sync_integration_source
from stoa_core.config import get_settings
from stoa_core.integrations.oauth_state import consume_oauth_state, create_oauth_state
from stoa_core.integrations.registry import get_connector, list_providers
from stoa_core.integrations.service import (
    create_connection,
    list_connections,
    list_sync_runs,
    oauth_redirect_uri_for,
    revoke_connection,
)
from stoa_core.redis.sse import read_events_since

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


class ConnectCredentialsBody(BaseModel):
    credentials: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None


class CsvImportBody(BaseModel):
    title: str = Field(default="CSV import", max_length=300)
    content: str = Field(min_length=1, max_length=10 * 1024 * 1024)
    column_mapping: dict[str, str | None] | None = None


@router.get("/providers")
def get_providers(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    return {"providers": [p.__dict__ for p in list_providers()]}


@router.get("/sources")
def get_sources(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    return {"connections": list_connections(scope.org_id)}


@router.get("/connect/{provider}")
def start_oauth(
    provider: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, str]:
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    connector = get_connector(provider)
    info = connector.provider_info()
    if info.auth_type != "oauth":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provider does not use OAuth")
    redirect_uri = oauth_redirect_uri_for(provider)
    state = create_oauth_state(scope.org_id, scope.user_id, provider)
    url = connector.oauth_authorize_url(state, redirect_uri)
    if not url:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "OAuth not configured for provider")
    return {"authorize_url": url}


@router.get("/callback/{provider}")
def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    oauth_state = consume_oauth_state(state)
    if not oauth_state or oauth_state.get("provider") != provider:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")
    org_id = oauth_state["org_id"]
    user_id = oauth_state.get("user_id")
    connector = get_connector(provider)
    redirect_uri = oauth_redirect_uri_for(provider)
    token_data = connector.exchange_oauth_code(code, redirect_uri)
    credentials = {k: v for k, v in token_data.items() if k != "provider_metadata"}
    metadata = token_data.get("provider_metadata") or {}
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
    sync_integration_source.delay(conn["id"], org_id, full_backfill=True)
    app_url = get_settings().app_base_url.rstrip("/")
    return RedirectResponse(f"{app_url}/data?connected={provider}")


@router.post("/sources/{provider}/connect")
def connect_with_credentials(
    provider: str,
    body: ConnectCredentialsBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
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
    sync_integration_source.delay(conn["id"], scope.org_id, full_backfill=True)
    return {"connection": conn}


@router.post("/sources/{connection_id}/sync")
def trigger_sync(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
    full: bool = Query(False),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="integrations")
    sync_integration_source.delay(connection_id, scope.org_id, full_backfill=full)
    return {"status": "queued", "connection_id": connection_id}


@router.delete("/sources/{connection_id}")
def disconnect(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, str]:
    require_permission(scope, "data_sources:write")
    revoke_connection(connection_id, scope.org_id)
    write_audit(scope.org_id, scope.user_id, "integration.revoked", "integration_connection", connection_id)
    return {"status": "revoked"}


@router.get("/sources/{connection_id}/runs")
def get_sync_runs(
    connection_id: str,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    return {"runs": list_sync_runs(connection_id, scope.org_id)}


@router.post("/csv/detect")
def detect_csv_columns(
    body: CsvImportBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    require_permission(scope, "data_sources:read")
    from stoa_core.integrations.csv_structured import CSV_FIELD_DEFINITIONS, detect_columns, parse_csv_content

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
    require_permission(scope, "data_sources:read")

    async def _gen():
        last_id = request.headers.get("Last-Event-ID", "0-0")
        async for msg_id, data in read_events_since("integration", connection_id, last_id):
            yield f"id: {msg_id}\ndata: {__import__('json').dumps(data)}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.post("/webhooks/hubspot")
async def hubspot_webhook(request: Request) -> dict[str, str]:
    """HubSpot webhook receiver — queues sync for matching portal."""
    from stoa_core.db.supabase import get_supabase_admin

    try:
        payload = await request.json()
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
        .select("id, org_id")
        .eq("provider", "hubspot")
        .eq("status", "active")
        .limit(10)
        .execute()
    )
    for row in res.data or []:
        sync_integration_source.delay(row["id"], row["org_id"])
    return {"status": "queued", "count": len(res.data or [])}
