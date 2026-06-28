"""
File: services/core/src/stoa_core/rag/answer.py
Layer: Core Retrieval / RAG
Purpose: Implements answer behavior for the core retrieval / rag.
Dependencies: stoa_core
"""


from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_text
from stoa_core.rag.cache import cache_answer, get_cached_answer

ANSWER_SYSTEM = """You are a marketing intelligence analyst. Answer using ONLY the provided context.
Do not include inline citation markers, bracketed source IDs, or document references in the answer.
If insufficient evidence, say so. Be concise and actionable. Do not invent facts."""

ANSWER_UNAVAILABLE = "Unable to generate an answer right now. Please try again."
EMBEDDING_UNAVAILABLE = (
    "Search is temporarily unavailable. Please try again in a moment."
)
NO_DATA_INGESTED = (
    "I don't have enough ingested customer data yet. "
    "Upload transcripts, reviews, or CRM exports first."
)
NO_MATCHES = (
    "I couldn't find relevant evidence for that question in your workspace data. "
    "Try rephrasing or add more customer data and integrations."
)


def answer_question(
    question: str,
    context: list[dict[str, Any]],
    *,
    org_id: str | None = None,
    kinds: list[str] | None = None,
    use_cache: bool = True,
    retrieval_status: str = "ok",
) -> str:
    """Handles answer question logic for the surrounding Stoa workflow."""
    result = try_answer_question(
        question,
        context,
        org_id=org_id,
        kinds=kinds,
        use_cache=use_cache,
        retrieval_status=retrieval_status,
    )
    return result if result is not None else ANSWER_UNAVAILABLE


def try_answer_question(
    question: str,
    context: list[dict[str, Any]],
    *,
    org_id: str | None = None,
    kinds: list[str] | None = None,
    use_cache: bool = True,
    retrieval_status: str = "ok",
) -> str | None:
    """Like answer_question, but returns None when the LLM produced nothing."""
    if retrieval_status == "embedding_unavailable":
        return EMBEDDING_UNAVAILABLE

    if org_id and use_cache:
        cached = get_cached_answer(org_id, question, kinds)
        if cached:
            return cached

    if not context:
        if retrieval_status == "no_matches":
            return NO_MATCHES
        return NO_DATA_INGESTED

    lines = []
    for item in context[:30]:
        ref = item.get("ref", "unknown")
        text = item.get("text", "")
        lines.append(f"[{ref}] {text}")
    user = f"Question: {question}\n\nContext:\n" + "\n".join(lines)
    answer, _provider = invoke_text(ANSWER_SYSTEM, user, task_name="synthesize")
    if answer and org_id and use_cache:
        cache_answer(org_id, question, kinds, answer)
    return answer or None
