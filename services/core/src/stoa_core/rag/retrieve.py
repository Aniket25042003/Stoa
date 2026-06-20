"""
File: services/core/src/stoa_core/rag/retrieve.py
Layer: Core Retrieval / RAG
Purpose: Implements retrieve behavior for the core retrieval / rag.
Dependencies: Supabase, stoa_core
"""


from __future__ import annotations

import logging
import re
from typing import Any

from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.ingestion.embed import embed_query
from stoa_core.rag.cache import (
    cache_query_embedding,
    cache_retrieval_result,
    get_cached_query_embedding,
    get_cached_retrieval_result,
)
from stoa_core.rag.rerank import rerank_candidates

logger = logging.getLogger(__name__)


def _normalize_query(query: str) -> str:
    """Handles  normalize query logic for the surrounding Stoa workflow.

    Args:
        query (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    return re.sub(r"\s+", " ", query.strip().lower())


def _match_knowledge_rpc(
    org_id: str,
    query_embedding: list[float],
    query_text: str,
    kinds: list[str] | None,
    match_count: int,
    rrf_k: int,
) -> list[dict[str, Any]]:
    """Handles  match knowledge rpc logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        query_embedding (list[float]): Input value used by this workflow step.
        query_text (str): Input value used by this workflow step.
        kinds (list[str] | None): Input value used by this workflow step.
        match_count (int): Input value used by this workflow step.
        rrf_k (int): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    params: dict[str, Any] = {
        "p_org_id": org_id,
        "p_query_embedding": query_embedding,
        "p_query_text": query_text,
        "p_kinds": kinds,
        "p_match_count": match_count,
        "p_rrf_k": rrf_k,
    }
    res = sb.rpc("match_knowledge", params).execute()
    return res.data or []


def _mmr_dedup(
    candidates: list[dict[str, Any]],
    *,
    lambda_mult: float = 0.7,
    max_items: int,
) -> list[dict[str, Any]]:
    """Maximal Marginal Relevance — reduce near-duplicate chunks."""
    if len(candidates) <= max_items:
        return candidates

    selected: list[dict[str, Any]] = []
    remaining = list(candidates)

    def _sim(a: str, b: str) -> float:
        """Handles  sim logic for the surrounding Stoa workflow.

        Args:
            a (str): Input value used by this workflow step.
            b (str): Input value used by this workflow step.

        Returns:
            float: Result produced for the caller.
        """
        aw = set(a.lower().split())
        bw = set(b.lower().split())
        if not aw or not bw:
            return 0.0
        return len(aw & bw) / len(aw | bw)

    while remaining and len(selected) < max_items:
        best_idx = 0
        best_score = -1.0
        for i, cand in enumerate(remaining):
            relevance = float(cand.get("rerank_score") or cand.get("rrf_score") or 0.0)
            redundancy = 0.0
            if selected:
                redundancy = max(
                    _sim(cand.get("content", ""), s.get("content", "")) for s in selected
                )
            score = lambda_mult * relevance - (1 - lambda_mult) * redundancy
            if score > best_score:
                best_score = score
                best_idx = i
        selected.append(remaining.pop(best_idx))

    return selected


def _apply_token_budget(
    candidates: list[dict[str, Any]],
    token_budget: int,
) -> list[dict[str, Any]]:
    """Handles  apply token budget logic for the surrounding Stoa workflow.

    Args:
        candidates (list[dict[str, Any]]): Input value used by this workflow step.
        token_budget (int): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    out: list[dict[str, Any]] = []
    used = 0
    for cand in candidates:
        text = cand.get("content", "")
        tokens = cand.get("token_count") or max(1, len(text) // 4)
        if used + tokens > token_budget and out:
            break
        out.append(cand)
        used += tokens
    return out


def _to_context_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Handles  to context items logic for the surrounding Stoa workflow.

    Args:
        candidates (list[dict[str, Any]]): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    context: list[dict[str, Any]] = []
    for cand in candidates:
        chunk_id = cand.get("chunk_id") or cand.get("id")
        item_id = cand.get("item_id")
        kind = cand.get("kind", "unknown")
        title = cand.get("item_title") or ""
        ref = f"kb:{kind}:{item_id}:{chunk_id}"
        text = str(cand.get("content", ""))
        context.append(
            {
                "ref": ref,
                "text": text,
                "score": float(cand.get("rerank_score") or cand.get("rrf_score") or 0.0),
                "kind": kind,
                "item_title": title,
                "chunk_id": chunk_id,
                "item_id": item_id,
                "token_count": cand.get("token_count") or max(1, len(text) // 4),
            }
        )
    return context


def retrieve_context(
    org_id: str,
    query: str,
    *,
    kinds: list[str] | None = None,
    k: int | None = None,
    token_budget: int | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve ranked, token-budgeted context for an LLM call."""
    settings = get_settings()
    final_k = k or settings.retrieval_final_k
    budget = token_budget or settings.retrieval_token_budget
    normalized = _normalize_query(query)

    if use_cache:
        cached = get_cached_retrieval_result(org_id, normalized, kinds)
        if cached is not None:
            return cached

    query_emb = get_cached_query_embedding(org_id, normalized) if use_cache else None
    if query_emb is None:
        query_emb = embed_query(query)
        if use_cache:
            cache_query_embedding(org_id, normalized, query_emb)

    candidates = _match_knowledge_rpc(
        org_id,
        query_emb,
        query,
        kinds,
        settings.retrieval_candidate_k,
        settings.retrieval_rrf_k,
    )

    if not candidates:
        return []

    reranked = rerank_candidates(query, candidates, top_k=final_k * 2)
    deduped = _mmr_dedup(reranked, max_items=final_k * 2)
    trimmed = _apply_token_budget(deduped, budget)
    context = _to_context_items(trimmed[:final_k])

    if use_cache:
        cache_retrieval_result(org_id, normalized, kinds, context)

    return context
