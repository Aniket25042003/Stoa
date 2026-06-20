"""
File: services/core/src/stoa_core/rag/rerank.py
Layer: Core Retrieval / RAG
Purpose: Implements rerank behavior for the core retrieval / rag.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any

from stoa_core.config import get_settings
from stoa_core.llm.router import invoke_json

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# BM25 hyperparameters (Okapi BM25)
_BM25_K1 = 1.5
_BM25_B = 0.75
_BM25_MAX_CANDIDATES = 60
_LLM_MAX_CANDIDATES = 40
_LLM_SNIPPET_CHARS = 500


def rerank_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Rerank hybrid-search candidates via Cohere, then Vertex LLM, then BM25."""
    if not candidates:
        return []
    settings = get_settings()
    k = top_k or settings.retrieval_final_k

    result = _cohere_rerank(query, candidates, top_k=k)
    if result is not None:
        logger.debug("Reranked %d candidates with Cohere", len(result))
        return result

    result = _vertex_batch_llm_rerank(query, candidates, top_k=k)
    if result is not None:
        logger.debug("Reranked %d candidates with Vertex batch LLM", len(result))
        return result

    logger.debug("Falling back to BM25 rerank for %d candidates", len(candidates))
    return _bm25_rerank(query, candidates, top_k=k)


def _cohere_rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]] | None:
    """Handles  cohere rerank logic for the surrounding Stoa workflow.

    Args:
        query (str): Input value used by this workflow step.
        candidates (list[dict[str, Any]]): Input value used by this workflow step.
        top_k (int): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]] | None: Result produced for the caller.
    """
    settings = get_settings()
    api_key = settings.cohere_api_key
    if not api_key:
        return None
    try:
        import cohere

        client = cohere.ClientV2(api_key=api_key)
        pool = candidates[:_BM25_MAX_CANDIDATES]
        docs = [c.get("content", "") for c in pool]
        response = client.rerank(
            model=settings.cohere_rerank_model,
            query=query,
            documents=docs,
            top_n=min(top_k, len(docs)),
        )
        out: list[dict[str, Any]] = []
        for hit in response.results:
            item = dict(pool[hit.index])
            item["rerank_score"] = hit.relevance_score
            item["rerank_method"] = "cohere"
            out.append(item)
        return out
    except Exception as exc:
        logger.warning("Cohere rerank failed: %s", exc)
        return None


def _vertex_batch_llm_rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]] | None:
    """Single Vertex LLM call ranking all candidate chunks at once."""
    pool = candidates[:_LLM_MAX_CANDIDATES]
    if not pool:
        return None

    system = (
        "You rerank document chunks for a retrieval system. "
        "Given a user query and numbered candidates, return the candidate indices "
        "ordered from most to least relevant. "
        'Return JSON only: {"ranked_indices": [0, 2, 1, ...]}. '
        "Include every index at most once. Prefer chunks with direct evidence for the query."
    )
    payload = {
        "query": query,
        "candidates": [
            {
                "index": i,
                "content": str(c.get("content", ""))[:_LLM_SNIPPET_CHARS],
                "kind": c.get("kind"),
                "title": c.get("item_title"),
            }
            for i, c in enumerate(pool)
        ],
    }
    parsed, provider = invoke_json(system, payload, task_name="classify", max_chars=24000)
    if not parsed:
        logger.warning("Vertex batch LLM rerank returned no JSON (provider=%s)", provider)
        return None

    indices = parsed.get("ranked_indices") or []
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for idx in indices:
        if not isinstance(idx, int) or idx < 0 or idx >= len(pool) or idx in seen:
            continue
        seen.add(idx)
        item = dict(pool[idx])
        item["rerank_score"] = 1.0 - len(out) * 0.01
        item["rerank_method"] = "vertex_llm"
        out.append(item)
        if len(out) >= top_k:
            break

    if not out:
        return None
    return out


def _tokenize(text: str) -> list[str]:
    """Handles  tokenize logic for the surrounding Stoa workflow.

    Args:
        text (str): Input value used by this workflow step.

    Returns:
        list[str]: Result produced for the caller.
    """
    return _TOKEN_RE.findall(text.lower())


def _bm25_rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    """Lightweight BM25 rerank — keyword-heavy fallback, no ML models."""
    pool = candidates[:_BM25_MAX_CANDIDATES]
    query_terms = _tokenize(query)
    if not query_terms or not pool:
        return _attach_scores(pool[:top_k], method="bm25", scores=None)

    doc_tokens = [_tokenize(c.get("content", "")) for c in pool]
    doc_lens = [len(t) or 1 for t in doc_tokens]
    avgdl = sum(doc_lens) / len(doc_lens)
    n_docs = len(pool)

    # Document frequency per query term
    df: Counter[str] = Counter()
    for terms in doc_tokens:
        for term in set(terms):
            if term in query_terms:
                df[term] += 1

    query_tf = Counter(query_terms)
    scores: list[float] = []
    for terms, doc_len in zip(doc_tokens, doc_lens):
        tf = Counter(terms)
        score = 0.0
        for term, qf in query_tf.items():
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            idf = math.log((n_docs - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1.0)
            denom = freq + _BM25_K1 * (1.0 - _BM25_B + _BM25_B * doc_len / avgdl)
            score += idf * (freq * (_BM25_K1 + 1.0)) / denom
        scores.append(score)

    ranked = sorted(zip(pool, scores), key=lambda x: x[1], reverse=True)
    out: list[dict[str, Any]] = []
    for cand, score in ranked[:top_k]:
        item = dict(cand)
        item["rerank_score"] = score
        item["rerank_method"] = "bm25"
        out.append(item)
    return out


def _attach_scores(
    candidates: list[dict[str, Any]],
    *,
    method: str,
    scores: list[float] | None,
) -> list[dict[str, Any]]:
    """Handles  attach scores logic for the surrounding Stoa workflow.

    Args:
        candidates (list[dict[str, Any]]): Input value used by this workflow step.
        method (str): Input value used by this workflow step.
        scores (list[float] | None): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    out: list[dict[str, Any]] = []
    for i, cand in enumerate(candidates):
        item = dict(cand)
        item["rerank_method"] = method
        if scores is not None:
            item["rerank_score"] = scores[i]
        else:
            item["rerank_score"] = float(cand.get("rrf_score") or 0.0)
        out.append(item)
    return out
