"""Precomputed proactive insights for common intelligence questions."""

from __future__ import annotations

from typing import Any

from stoa_core.rag.answer import answer_question
from stoa_core.rag.retrieve import retrieve_context

COMMON_QUESTIONS: list[dict[str, str]] = [
    {
        "key": "top_converting_customers",
        "title": "Who are our highest-converting customers?",
        "question": "Who are our highest-converting customers? Describe segments with evidence.",
    },
    {
        "key": "top_pain_points",
        "title": "What are the top customer pain points?",
        "question": "What pain points appear most frequently across our customer data?",
    },
    {
        "key": "common_objections",
        "title": "What objections come up most in sales?",
        "question": "What objections appear most frequently in customer conversations?",
    },
    {
        "key": "buying_triggers",
        "title": "What triggers customers to buy?",
        "question": "What buying triggers and decision drivers appear most often?",
    },
    {
        "key": "win_loss_themes",
        "title": "What win/loss themes stand out?",
        "question": "What win and loss themes emerge from the available customer evidence?",
    },
]

INTELLIGENCE_KINDS = ["document", "company_profile", "icp_profile"]


def precompute_answers(org_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in COMMON_QUESTIONS:
        context = retrieve_context(org_id, item["question"], kinds=INTELLIGENCE_KINDS)
        if not context:
            continue
        answer = answer_question(item["question"], context)
        results.append(
            {
                "key": item["key"],
                "title": item["title"],
                "content": {"answer": answer},
                "citations": [c["ref"] for c in context[:10]],
            }
        )
    return results


def build_executive_summary(org_id: str, org_name: str) -> dict[str, Any]:
    context = retrieve_context(
        org_id,
        f"Executive summary of marketing intelligence for {org_name}",
        kinds=INTELLIGENCE_KINDS,
    )
    if not context:
        return {
            "summary": f"No customer intelligence ingested yet for {org_name}. Add documents in the Data hub.",
            "citations": [],
        }
    summary = answer_question(
        f"Write a concise executive summary of marketing intelligence for {org_name}. "
        "Cover ICP signals, top pains, objections, and one recommended next action.",
        context,
    )
    return {"summary": summary, "citations": [c["ref"] for c in context[:8]]}
