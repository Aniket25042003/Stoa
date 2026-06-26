"""Query preparation for retrieval: heuristics, cheap LLM rewrite, multi-query merge."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from stoa_core.config import get_settings
from stoa_core.llm.router import invoke_json
from stoa_core.rag.cache import cache_query_rewrite, get_cached_query_rewrite
from stoa_core.rag.retrieve import _apply_token_budget, _normalize_query, retrieve_context

logger = logging.getLogger(__name__)

MAX_SEARCH_QUERIES = 3
SHORT_QUERY_TOKEN_LIMIT = 12
SHORT_QUERY_CHAR_LIMIT = 60

_DEICTIC_PATTERN = re.compile(
    r"\b(it|its|they|them|their|that|those|this|these|he|she|him|her|"
    r"the same|last one|previous|earlier|above|there)\b",
    re.IGNORECASE,
)

REWRITE_SYSTEM = """You expand short or context-dependent user questions into search queries
for a marketing intelligence knowledge base (CRM deals, customer signals, campaigns,
competitive intel, documents, analytics).

Return JSON:
{
  "standalone_question": "self-contained question preserving user intent",
  "search_queries": ["query1", "query2"]
}

Rules:
- Produce 1-3 search_queries with domain vocabulary (deals, revenue, ICP, campaigns, etc.)
- Resolve pronouns using recent conversation when provided
- Do not invent facts; only clarify retrieval intent
- search_queries must be distinct angles on the same intent"""


@dataclass
class PreparedQuery:
    original_question: str
    standalone_question: str
    search_queries: list[str]
    rewrite_used: bool


def _token_count(text: str) -> int:
    return len(text.split())


def needs_query_rewrite(question: str, *, has_history: bool) -> bool:
    q = question.strip()
    if not q:
        return False
    if _token_count(q) < SHORT_QUERY_TOKEN_LIMIT or len(q) < SHORT_QUERY_CHAR_LIMIT:
        return True
    if has_history and _DEICTIC_PATTERN.search(q):
        return True
    return False


def _history_snippets(history: list[dict[str, Any]], *, limit: int = 4) -> list[str]:
    snippets: list[str] = []
    for row in history[-limit:]:
        role = str(row.get("role") or "user")
        content = str(row.get("content") or "").strip().replace("\n", " ")
        if content:
            snippets.append(f"{role}: {content[:240]}")
    return snippets


def _rewrite_query(
    org_id: str,
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
    org_hints: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> PreparedQuery:
    normalized = _normalize_query(question)
    history = history or []
    cache_key_extra = "|".join(_history_snippets(history))

    if use_cache:
        cached = get_cached_query_rewrite(org_id, normalized, cache_key_extra)
        if cached:
            return PreparedQuery(
                original_question=question,
                standalone_question=cached.get("standalone_question") or question,
                search_queries=list(cached.get("search_queries") or [question]),
                rewrite_used=True,
            )

    payload: dict[str, Any] = {
        "question": question,
        "recent_messages": _history_snippets(history),
    }
    if org_hints:
        payload["org_hints"] = org_hints

    parsed, _provider = invoke_json(REWRITE_SYSTEM, payload, task_name="query_rewrite")
    if parsed:
        standalone = str(parsed.get("standalone_question") or question).strip() or question
        raw_queries = parsed.get("search_queries")
        queries: list[str] = []
        if isinstance(raw_queries, list):
            for item in raw_queries:
                if isinstance(item, str) and item.strip():
                    queries.append(item.strip())
        if standalone not in queries:
            queries.insert(0, standalone)
        queries = queries[:MAX_SEARCH_QUERIES]
        if use_cache:
            cache_query_rewrite(
                org_id,
                normalized,
                cache_key_extra,
                {"standalone_question": standalone, "search_queries": queries},
            )
        return PreparedQuery(
            original_question=question,
            standalone_question=standalone,
            search_queries=queries,
            rewrite_used=True,
        )

    logger.warning("Query rewrite returned no JSON; using original question")
    return PreparedQuery(
        original_question=question,
        standalone_question=question,
        search_queries=[question],
        rewrite_used=False,
    )


def prepare_query(
    org_id: str,
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
    org_hints: dict[str, Any] | None = None,
    force_rewrite: bool = False,
    use_cache: bool = True,
) -> PreparedQuery:
    has_history = bool(history)
    if force_rewrite or needs_query_rewrite(question, has_history=has_history):
        return _rewrite_query(
            org_id,
            question,
            history=history,
            org_hints=org_hints,
            use_cache=use_cache,
        )
    return PreparedQuery(
        original_question=question,
        standalone_question=question,
        search_queries=[question],
        rewrite_used=False,
    )


def _merge_context_items(
    batches: list[list[dict[str, Any]]],
    *,
    final_k: int,
    token_budget: int,
) -> list[dict[str, Any]]:
    seen_refs: set[str] = set()
    merged: list[dict[str, Any]] = []
    for batch in batches:
        for item in batch:
            ref = str(item.get("ref") or "")
            if ref and ref in seen_refs:
                continue
            if ref:
                seen_refs.add(ref)
            merged.append(item)
    merged.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    as_cands = [
        {
            "content": item.get("text", ""),
            "token_count": item.get("token_count"),
            "rerank_score": item.get("score"),
            **item,
        }
        for item in merged
    ]
    trimmed = _apply_token_budget(as_cands, token_budget)
    return [
        {
            "ref": c.get("ref"),
            "text": c.get("text") or c.get("content", ""),
            "score": c.get("score") or c.get("rerank_score", 0.0),
            "kind": c.get("kind"),
            "item_title": c.get("item_title"),
            "chunk_id": c.get("chunk_id"),
            "item_id": c.get("item_id"),
            "token_count": c.get("token_count"),
        }
        for c in trimmed[:final_k]
    ]


def retrieve_context_prepared(
    org_id: str,
    question: str,
    *,
    kinds: list[str] | None = None,
    k: int | None = None,
    token_budget: int | None = None,
    conversation_id: str | None = None,
    history: list[dict[str, Any]] | None = None,
    org_hints: dict[str, Any] | None = None,
    use_cache: bool = True,
) -> tuple[list[dict[str, Any]], PreparedQuery]:
    """Prepare query then retrieve; merges results from multiple search queries."""
    settings = get_settings()
    final_k = k or settings.retrieval_final_k
    budget = token_budget or settings.retrieval_token_budget

    prepared = prepare_query(
        org_id,
        question,
        history=history,
        org_hints=org_hints,
        use_cache=use_cache,
    )

    batches: list[list[dict[str, Any]]] = []
    for search_q in prepared.search_queries:
        ctx = retrieve_context(
            org_id,
            search_q,
            kinds=kinds,
            k=final_k,
            token_budget=budget,
            conversation_id=conversation_id,
            use_cache=use_cache,
        )
        if ctx:
            batches.append(ctx)

    if not batches:
        return [], prepared
    if len(batches) == 1:
        return batches[0][:final_k], prepared
    return _merge_context_items(batches, final_k=final_k, token_budget=budget), prepared
