"""Company knowledge base: Vertex embeddings + Supabase RPC (pgvector)."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

logger = logging.getLogger(__name__)

KB_EMBEDDING_DIM = 768

KnowledgeKind = Literal[
    "competitor",
    "positioning",
    "icp",
    "channel",
    "learning",
    "asset_outcome",
    "brand_decision",
    "risk",
    "other",
]
SourceSystem = Literal["gtm", "marketing"]


def _supabase():
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception as exc:  # pragma: no cover
        logger.debug("Supabase client unavailable: %s", exc)
        return None


def embed_text(text: str) -> list[float] | None:
    """768-dim embedding via Vertex (text-embedding-004 by default)."""
    text = (text or "").strip()
    if not text:
        return None
    model = (os.getenv("MKT_EMBED_MODEL") or "text-embedding-004").strip()
    project = (os.getenv("GTM_VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
    location = (os.getenv("GTM_VERTEX_LOCATION") or "us-central1").strip()
    if not project:
        logger.warning("embed_text: missing GTM_VERTEX_PROJECT / GOOGLE_CLOUD_PROJECT")
        return None
    try:
        from langchain_google_vertexai import VertexAIEmbeddings

        emb = VertexAIEmbeddings(
            model_name=model,
            project=project,
            location=location,
        )
        vec = emb.embed_query(text[:8000])
        if not isinstance(vec, list) or not vec:
            return None
        if len(vec) == KB_EMBEDDING_DIM:
            return vec
        if len(vec) > KB_EMBEDDING_DIM:
            return vec[:KB_EMBEDDING_DIM]
        logger.warning("embed_text: dim %s != %s; skipping embedding for KB", len(vec), KB_EMBEDDING_DIM)
        return None
    except Exception as exc:
        logger.warning("embed_text failed: %s", exc)
        return None


def kb_insert(
    company_id: str,
    kind: KnowledgeKind | str,
    title: str,
    content: str,
    *,
    tags: list[str] | None = None,
    source_system: SourceSystem | str | None = None,
    source_run_id: str | None = None,
    source_chat_id: str | None = None,
    embedding: list[float] | None = None,
) -> str | None:
    """Insert a knowledge row (RPC). Embeds ``content`` if ``embedding`` is None."""
    sb = _supabase()
    if sb is None:
        return None
    emb = embedding
    if emb is None and content:
        emb = embed_text(f"{title}\n{content}")
    if emb is not None:
        if len(emb) > KB_EMBEDDING_DIM:
            emb = emb[:KB_EMBEDDING_DIM]
        elif len(emb) < KB_EMBEDDING_DIM:
            emb = None  # avoid wrong-dimension vector cast in DB
    try:
        res = sb.rpc(
            "kb_insert_row",
            {
                "p_company_id": company_id,
                "p_kind": str(kind),
                "p_title": title or "",
                "p_content": content or "",
                "p_embedding": emb,
                "p_tags": tags or [],
                "p_source_system": source_system,
                "p_source_run_id": source_run_id,
                "p_source_chat_id": source_chat_id,
            },
        ).execute()
        data = res.data
        if isinstance(data, str):
            return data
        if isinstance(data, list) and data:
            return str(data[0])
        return None
    except Exception as exc:
        logger.warning("kb_insert failed: %s", exc)
        return None


def kb_search(
    company_id: str,
    query: str,
    *,
    k: int = 8,
    kinds: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Semantic search when embeddings work; else ILIKE text RPC."""
    sb = _supabase()
    if sb is None:
        return []
    q = (query or "").strip()
    vec = embed_text(q) if q else None
    try:
        if vec and len(vec) == KB_EMBEDDING_DIM:
            res = sb.rpc(
                "kb_match_company_knowledge",
                {
                    "p_company_id": company_id,
                    "p_query_embedding": vec,
                    "p_match_count": k,
                    "p_kinds": kinds,
                },
            ).execute()
        else:
            res = sb.rpc(
                "kb_search_company_knowledge_text",
                {
                    "p_company_id": company_id,
                    "p_query": q or None,
                    "p_match_count": k,
                    "p_kinds": kinds,
                },
            ).execute()
        rows = res.data or []
        return [dict(r) for r in rows] if isinstance(rows, list) else []
    except Exception as exc:
        logger.warning("kb_search failed: %s", exc)
        return []


def kb_facts(
    company_id: str,
    kind: KnowledgeKind | str | None = None,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Structured list of knowledge rows (newest first)."""
    sb = _supabase()
    if sb is None:
        return []
    try:
        q = sb.table("company_knowledge").select("*").eq("company_id", company_id)
        if kind:
            q = q.eq("kind", str(kind))
        res = q.order("updated_at", desc=True).limit(limit).execute()
        return list(res.data or [])
    except Exception as exc:
        logger.warning("kb_facts failed: %s", exc)
        return []


def kb_format_for_prompt(rows: list[dict[str, Any]], max_chars: int = 12000) -> str:
    """Compact string for LLM context."""
    parts: list[str] = []
    n = 0
    for r in rows:
        line = f"### {r.get('kind', '')}: {r.get('title', '')}\n{r.get('content', '')}\n"
        if n + len(line) > max_chars:
            break
        parts.append(line)
        n += len(line)
    return "\n".join(parts).strip() or "(no knowledge base entries yet)"
