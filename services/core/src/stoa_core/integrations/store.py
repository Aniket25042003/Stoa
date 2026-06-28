"""
File: services/core/src/stoa_core/integrations/store.py
Layer: Core Integration Connectors
Purpose: Implements store behavior for the core integration connectors.
Dependencies: Supabase, stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.ingestion.chunk import chunk_text
from stoa_core.ingestion.extract import extract_signals
from stoa_core.integrations.textify import (
    account_to_text,
    contact_to_text,
    deal_to_text,
    interaction_to_text,
)
from stoa_core.rag.ingest import ingest_knowledge

logger = logging.getLogger(__name__)

KB_KIND_MAP = {
    "account": "crm_account",
    "contact": "crm_contact",
    "deal": "crm_deal",
    "interaction": None,  # resolved from interaction_type
}

INTERACTION_KIND_MAP = {
    "call_transcript": "call_transcript",
    "support_ticket": "support_ticket",
    "review": "review",
    "note": "document",
    "email": "document",
    "meeting": "call_transcript",
}


def upsert_account(org_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Handles upsert account logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    payload = {**row, "org_id": org_id}
    res = (
        sb.table("canonical_accounts")
        .upsert(payload, on_conflict="org_id,external_source,external_id")
        .execute()
    )
    saved = (res.data or [None])[0]
    if saved:
        _ingest_canonical(org_id, "account", saved, account_to_text(saved))
    return saved


def upsert_contact(org_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Handles upsert contact logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    payload = {**row, "org_id": org_id}
    res = (
        sb.table("canonical_contacts")
        .upsert(payload, on_conflict="org_id,external_source,external_id")
        .execute()
    )
    saved = (res.data or [None])[0]
    if saved:
        _ingest_canonical(org_id, "contact", saved, contact_to_text(saved))
    return saved


def upsert_deal(org_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Handles upsert deal logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    payload = {**row, "org_id": org_id}
    res = (
        sb.table("canonical_deals")
        .upsert(payload, on_conflict="org_id,external_source,external_id")
        .execute()
    )
    saved = (res.data or [None])[0]
    if saved:
        _ingest_canonical(org_id, "deal", saved, deal_to_text(saved))
    return saved


def upsert_interaction(org_id: str, row: dict[str, Any], *, extract: bool = True) -> dict[str, Any] | None:
    """Handles upsert interaction logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        row (dict[str, Any]): Input value used by this workflow step.
        extract (bool): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    payload = {**row, "org_id": org_id}
    res = (
        sb.table("canonical_interactions")
        .upsert(payload, on_conflict="org_id,external_source,external_id")
        .execute()
    )
    saved = (res.data or [None])[0]
    if not saved:
        return None
    itype = saved.get("interaction_type") or "note"
    kind = INTERACTION_KIND_MAP.get(itype, "document")
    source = saved.get("external_source") or "unknown"
    ext_id = saved.get("external_id") or saved.get("id")
    text = interaction_to_text(saved)
    ingest_knowledge(
        org_id,
        kind=kind,
        title=saved.get("title") or f"{itype} {ext_id}",
        text=text,
        feature_origin="integrations",
        uri=f"{source}:{itype}:{ext_id}",
        metadata={"interaction_type": itype, "interaction_id": saved.get("id")},
    )
    if extract and text.strip():
        _extract_interaction_signals(org_id, saved, text)
    return saved


def _ingest_canonical(org_id: str, entity: str, saved: dict[str, Any], text: str) -> None:
    """Handles  ingest canonical logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        entity (str): Input value used by this workflow step.
        saved (dict[str, Any]): Input value used by this workflow step.
        text (str): Input value used by this workflow step.
    """
    kind = KB_KIND_MAP.get(entity)
    if not kind:
        return
    source = saved.get("external_source") or "unknown"
    ext_id = saved.get("external_id") or saved.get("id")
    ingest_knowledge(
        org_id,
        kind=kind,
        title=f"{entity.title()}: {saved.get('name') or ext_id}",
        text=text,
        feature_origin="integrations",
        uri=f"{source}:{entity}:{ext_id}",
        metadata={"entity": entity, f"canonical_{entity}_id": saved.get("id")},
    )


def _extract_interaction_signals(org_id: str, interaction: dict[str, Any], text: str) -> None:
    """Handles  extract interaction signals logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        interaction (dict[str, Any]): Input value used by this workflow step.
        text (str): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    interaction_id = interaction.get("id")
    source_type = interaction.get("external_source")
    for chunk in chunk_text(text):
        for sig in extract_signals(chunk.content, str(interaction_id or "")):
            sb.table("intelligence").insert(
                {
                    "org_id": org_id,
                    "interaction_id": interaction_id,
                    "source_type": source_type,
                    "kind": sig.get("kind"),
                    "content": sig.get("content"),
                    "confidence": sig.get("confidence", 0.5),
                    "evidence": {"quote": sig.get("evidence_quote", "")},
                }
            ).execute()
