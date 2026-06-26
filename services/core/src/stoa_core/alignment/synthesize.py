"""
File: services/core/src/stoa_core/alignment/synthesize.py
Layer: Core Alignment
Purpose: Synthesize alignment narratives from structured data + RAG.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.friction import collect_friction_signals
from stoa_core.alignment.questions import ALIGNMENT_KINDS, ALIGNMENT_QUESTIONS
from stoa_core.llm.router import invoke_text
from stoa_core.rag.answer import try_answer_question
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a GTM alignment analyst helping marketing and sales share one evidence-backed view. "
    "Be balanced — cite data for both sides. Keep answers concise (3-5 sentences)."
)


def precompute_alignment_answers(org_id: str) -> list[dict[str, Any]]:
    """Generate precomputed alignment insight answers."""
    summary = build_alignment_summary(org_id)
    friction = collect_friction_signals(org_id)
    if not summary.get("has_data") and not friction.get("top_objections"):
        return []

    context_blob = json.dumps({"summary": summary, "friction": friction}, default=str)[:5000]
    results: list[dict[str, Any]] = []

    for item in ALIGNMENT_QUESTIONS:
        kb_context = retrieve_context(org_id, item["question"], kinds=ALIGNMENT_KINDS)
        answer = try_answer_question(item["question"], kb_context)
        if answer is None:
            user_prompt = (
                f"Question: {item['question']}\n\n"
                f"Structured data:\n{context_blob}\n\n"
                f"Evidence:\n"
                + "\n".join(f"[{c['ref']}] {c['text'][:300]}" for c in kb_context[:15])
            )
            try:
                answer, _ = invoke_text(_SYSTEM, user_prompt, task_name="synthesize")
            except Exception:
                logger.exception("Alignment synthesis failed for %s", item["key"])
                continue
        if not answer:
            continue
        results.append(
            {
                "key": item["key"],
                "title": item["title"],
                "content": {"answer": answer},
                "citations": [c["ref"] for c in kb_context[:10]],
            }
        )

    if results:
        summary_text = "\n\n".join(
            f"## {r['title']}\n{r['content'].get('answer', '')}" for r in results
        )
        ingest_knowledge(
            org_id,
            kind="alignment_summary",
            title="Sales–marketing alignment summary",
            text=summary_text,
            feature_origin="alignment",
            uri=f"alignment:summary:{org_id}",
            metadata={"insight_count": len(results)},
        )

    return results
