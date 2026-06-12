"""Generic knowledge base write path."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any

from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.ingestion.chunk import chunk_text
from stoa_core.ingestion.embed import embed_texts
from stoa_core.rag.cache import bump_kb_version
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_knowledge(
    org_id: str,
    *,
    kind: str,
    title: str,
    text: str,
    feature_origin: str | None = None,
    metadata: dict[str, Any] | None = None,
    uri: str | None = None,
    source_id: str | None = None,
    summary: str | None = None,
    force: bool = False,
) -> dict[str, Any] | None:
    """Chunk, embed, and upsert a knowledge item + chunks. Idempotent on uri/content_hash."""
    text = redact_pii((text or "").strip())
    if not text:
        logger.info("Skipping ingest for empty text (org=%s kind=%s)", org_id, kind)
        return None

    sb = get_supabase_admin()
    settings = get_settings()
    text_hash = content_hash(text)
    meta = dict(metadata or {})

    existing_item = _find_existing_item(sb, org_id, uri=uri, text_hash=text_hash)
    if existing_item and not force:
        if existing_item.get("content_hash") == text_hash:
            logger.info("Skipping ingest — unchanged content (org=%s uri=%s)", org_id, uri)
            return existing_item

    item_id = existing_item["id"] if existing_item else str(uuid.uuid4())
    version = (existing_item.get("version") or 0) + 1 if existing_item else 1

    item_row = {
        "id": item_id,
        "org_id": org_id,
        "source_id": source_id,
        "kind": kind,
        "feature_origin": feature_origin,
        "title": title,
        "summary": summary,
        "content": text[:50000],
        "uri": uri,
        "content_hash": text_hash,
        "metadata": meta,
        "status": "active",
        "version": version,
    }

    if existing_item:
        sb.table("knowledge_items").update(item_row).eq("id", item_id).execute()
        sb.table("knowledge_chunks").delete().eq("item_id", item_id).execute()
    else:
        sb.table("knowledge_items").insert(item_row).execute()

    chunks = chunk_text(
        text,
        target_tokens=settings.chunk_target_tokens,
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    if not chunks:
        bump_kb_version(org_id)
        return item_row

    chunk_texts = [redact_pii(c.content) for c in chunks]
    embeddings = embed_texts(chunk_texts)

    chunk_rows = []
    for chunk, emb in zip(chunks, embeddings):
        chunk_rows.append(
            {
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "item_id": item_id,
                "chunk_index": chunk.chunk_index,
                "content": redact_pii(chunk.content),
                "token_count": chunk.token_count,
                "kind": kind,
                "metadata": meta,
                "content_hash": content_hash(chunk.content),
                "embedding": emb,
            }
        )

    # Batch insert in chunks of 50
    for i in range(0, len(chunk_rows), 50):
        sb.table("knowledge_chunks").insert(chunk_rows[i : i + 50]).execute()

    bump_kb_version(org_id)
    logger.info(
        "Ingested knowledge item %s (%s chunks) org=%s kind=%s",
        item_id,
        len(chunk_rows),
        org_id,
        kind,
    )
    return item_row


def _find_existing_item(
    sb: Any,
    org_id: str,
    *,
    uri: str | None,
    text_hash: str,
) -> dict[str, Any] | None:
    if uri:
        res = (
            sb.table("knowledge_items")
            .select("*")
            .eq("org_id", org_id)
            .eq("uri", uri)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
    res = (
        sb.table("knowledge_items")
        .select("*")
        .eq("org_id", org_id)
        .eq("content_hash", text_hash)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def profile_to_knowledge_text(
    org: dict[str, Any],
    *,
    user_profile: dict[str, Any] | None = None,
) -> str:
    """Serialize org + optional user onboarding fields into searchable knowledge text."""
    profile = org.get("profile") or {}
    parts = [
        f"Company: {org.get('name', '')}",
        f"Website: {org.get('website_url', '')}",
        f"Industry: {org.get('industry', '')}",
    ]
    if user_profile:
        for key, label in (
            ("role_type", "Owner role type"),
            ("job_title", "Owner job title"),
            ("use_case", "Primary use case"),
        ):
            val = user_profile.get(key)
            if val:
                parts.append(f"{label}: {val}")
    for key in (
        "target_customers",
        "business_model",
        "stage",
        "goals",
        "brand_voice",
        "known_competitors_notes",
        "company_size",
        "market",
    ):
        val = profile.get(key)
        if val:
            parts.append(f"{key.replace('_', ' ').title()}: {val}")
    return "\n".join(parts)


def json_artifact_to_text(data: dict[str, Any] | list[Any]) -> str:
    return json.dumps(data, indent=2, default=str)[:50000]
