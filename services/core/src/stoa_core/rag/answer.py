"""
File: services/core/src/stoa_core/rag/answer.py
Layer: Core Retrieval / RAG
Purpose: Implements answer behavior for the core retrieval / rag.
Dependencies: stoa_core
"""


from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_text

ANSWER_SYSTEM = """You are a marketing intelligence analyst. Answer using ONLY the provided context.
Cite evidence using [doc:ID] or [signal:ID] markers. If insufficient evidence, say so.
Be concise and actionable. Do not invent facts."""

ANSWER_UNAVAILABLE = "Unable to generate an answer right now. Please try again."


def answer_question(question: str, context: list[dict[str, Any]]) -> str:
    """Handles answer question logic for the surrounding Stoa workflow.

    Args:
        question (str): Input value used by this workflow step.
        context (list[dict[str, Any]]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    result = try_answer_question(question, context)
    return result if result is not None else ANSWER_UNAVAILABLE


def try_answer_question(question: str, context: list[dict[str, Any]]) -> str | None:
    """Like answer_question, but returns None when the LLM produced nothing
    so callers can skip persisting a failure message."""
    if not context:
        return (
            "I don't have enough ingested customer data yet. "
            "Upload transcripts, reviews, or CRM exports first."
        )
    lines = []
    for item in context[:30]:
        ref = item.get("ref", "unknown")
        text = item.get("text", "")
        lines.append(f"[{ref}] {text}")
    user = f"Question: {question}\n\nContext:\n" + "\n".join(lines)
    answer, _provider = invoke_text(ANSWER_SYSTEM, user, task_name="synthesize")
    return answer or None
