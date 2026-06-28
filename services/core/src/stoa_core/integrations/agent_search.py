"""Orchestrate scoped live connector searches for the unified agent."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from stoa_core.agent.evidence import EvidenceHit
from stoa_core.integrations.base import AgentSearchHit
from stoa_core.integrations.crypto import decrypt_credentials
from stoa_core.integrations.oauth_refresh import maybe_refresh_credentials
from stoa_core.integrations.registry import get_connector
from stoa_core.integrations.scope import scope_configured
from stoa_core.integrations.service import get_connection, list_connections

logger = logging.getLogger(__name__)

AGENT_SEARCH_TIMEOUT_SECONDS = 25


def _active_connection(org_id: str, provider: str) -> dict[str, Any] | None:
    for conn in list_connections(org_id):
        if conn.get("provider") != provider:
            continue
        if conn.get("status") in {"revoked", "disconnected"}:
            continue
        full = get_connection(str(conn["id"]), org_id)
        return full or conn
    return None


def _hits_to_evidence(hits: list[AgentSearchHit], *, entity_type: str | None) -> list[EvidenceHit]:
    out: list[EvidenceHit] = []
    for hit in hits:
        out.append(
            EvidenceHit(
                id=hit.id,
                title=hit.title,
                snippet=hit.snippet,
                uri=hit.uri or f"agent_evidence:{hit.provider}:{hit.id}",
                provider=hit.provider,
                source="connector",
                fetched_at=hit.fetched_at,
                entity_type=entity_type,
                meta=hit.meta,
            )
        )
    return out


def run_agent_search(
    org_id: str,
    provider: str,
    query: str,
    *,
    entity_type: str | None = None,
) -> tuple[list[EvidenceHit], str | None]:
    """Run live connector search; returns evidence hits and optional error message."""
    conn = _active_connection(org_id, provider)
    if not conn:
        return [], f"No active {provider} connection for this workspace"
    metadata = conn.get("provider_metadata") or {}
    if not scope_configured(provider, metadata):
        return [], f"{provider} access scope is not configured — configure integration access first"

    connector = get_connector(provider)
    if not connector.supports_agent_search():
        return [], f"Live search is not yet supported for {provider}"

    credentials = decrypt_credentials(conn.get("credentials_encrypted"))
    credentials = maybe_refresh_credentials(provider, credentials, metadata=metadata)

    try:
        hits = connector.agent_search(
            org_id,
            conn,
            credentials=credentials,
            query=query,
            entity_type=entity_type,
        )
    except NotImplementedError:
        return [], f"Live search is not yet supported for {provider}"
    except Exception as exc:
        logger.exception("agent_search failed org=%s provider=%s", org_id, provider)
        return [], str(exc)

    return _hits_to_evidence(hits, entity_type=entity_type), None


def agent_search_hit(
    *,
    id: str,
    title: str,
    snippet: str,
    provider: str,
    entity_type: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AgentSearchHit:
    now = datetime.now(UTC).isoformat()
    stable = id or title[:40]
    return AgentSearchHit(
        id=stable,
        title=title,
        snippet=snippet,
        uri=f"agent_evidence:{provider}:{stable}",
        provider=provider,
        fetched_at=now,
        meta=meta or {},
    )
