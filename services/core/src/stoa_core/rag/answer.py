"""RAG answer generation with citations."""

from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_text

ANSWER_SYSTEM = """You are a marketing intelligence analyst. Answer using ONLY the provided context.
Cite evidence using [doc:ID] or [signal:ID] markers. If insufficient evidence, say so.
Be concise and actionable. Do not invent facts."""


def answer_question(question: str, context: list[dict[str, Any]]) -> str:
    if not context:
        return "I don't have enough ingested customer data yet. Upload transcripts, reviews, or CRM exports first."
    lines = []
    for item in context[:30]:
        ref = item.get("ref", "unknown")
        text = item.get("text", "")
        lines.append(f"[{ref}] {text}")
    user = f"Question: {question}\n\nContext:\n" + "\n".join(lines)
    answer, _provider = invoke_text(ANSWER_SYSTEM, user, task_name="synthesize")
    return answer or "Unable to generate an answer right now. Please try again."
