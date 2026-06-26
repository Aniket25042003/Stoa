"""
File: services/core/src/stoa_core/analytics/synthesize.py
Layer: Core Analytics
Purpose: Synthesize campaign analysis narratives from structured metrics + RAG context.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.analytics.questions import CAMPAIGN_ANALYSIS_KINDS
from stoa_core.llm.router import invoke_text
from stoa_core.rag.answer import try_answer_question
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a marketing analytics analyst. Answer using only the provided metrics and evidence. "
    "Be specific with numbers. Cite evidence refs when present. "
    "Keep answers concise (3-5 sentences)."
)


def precompute_campaign_answers(org_id: str) -> list[dict[str, Any]]:
    """Generate precomputed campaign analysis insight answers."""
    summary = build_summary_metrics(org_id)
    if not summary.get("has_data"):
        return []

    metrics_context = json.dumps(summary, default=str)[:4000]
    results: list[dict[str, Any]] = []

    from stoa_core.analytics.questions import CAMPAIGN_ANALYSIS_QUESTIONS

    for item in CAMPAIGN_ANALYSIS_QUESTIONS:
        kb_context = retrieve_context(org_id, item["question"], kinds=CAMPAIGN_ANALYSIS_KINDS)
        user_prompt = (
            f"Question: {item['question']}\n\n"
            f"Structured metrics:\n{metrics_context}\n\n"
            f"Retrieved evidence:\n"
            + "\n".join(f"[{c['ref']}] {c['text'][:300]}" for c in kb_context[:15])
        )
        answer = try_answer_question(item["question"], kb_context)
        if answer is None and kb_context:
            try:
                answer, _ = invoke_text(_SYSTEM, user_prompt, task_name="synthesize")
            except Exception:
                logger.exception("Campaign analysis synthesis failed for %s", item["key"])
                continue
        if answer is None:
            answer, _ = invoke_text(
                _SYSTEM,
                f"Question: {item['question']}\n\nStructured metrics only:\n{metrics_context}",
                task_name="synthesize",
            )
        if not answer:
            continue
        results.append(
            {
                "key": item["key"],
                "title": item["title"],
                "content": {"answer": answer, "metrics_snapshot": summary},
                "citations": [c["ref"] for c in kb_context[:10]],
            }
        )
    return results
