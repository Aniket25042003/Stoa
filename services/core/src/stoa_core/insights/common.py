"""
File: services/core/src/stoa_core/insights/common.py
Layer: Application Source
Purpose: Implements common behavior for the application source.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

from stoa_core.rag.answer import try_answer_question
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

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

INTELLIGENCE_KINDS = [
    "document",
    "company_profile",
    "company_web_research",
    "icp_profile",
    "crm_account",
    "crm_contact",
    "crm_deal",
    "crm_landscape",
    "call_transcript",
    "support_ticket",
    "review",
    "review_themes",
    "product_analytics_summary",
    "competitive_snapshot",
    "competitive_research",
    "conversation_memory",
    "campaign_asset",
    "content_asset",
]


def precompute_answers(org_id: str) -> list[dict[str, Any]]:
    """Handles precompute answers logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    results: list[dict[str, Any]] = []
    for item in COMMON_QUESTIONS:
        context = retrieve_context(org_id, item["question"], kinds=INTELLIGENCE_KINDS)
        if not context:
            continue
        answer = try_answer_question(item["question"], context)
        if answer is None:
            logger.error(
                "Skipping insight %s for org %s: LLM produced no answer", item["key"], org_id
            )
            continue
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
    """Handles build executive summary logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        org_name (str): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    context = retrieve_context(
        org_id,
        f"Executive summary of marketing intelligence for {org_name}",
        kinds=INTELLIGENCE_KINDS,
    )
    if not context:
        return {
            "summary": (
                f"No customer intelligence ingested yet for {org_name}. "
                "Add documents in the Data hub."
            ),
            "citations": [],
        }
    summary = try_answer_question(
        f"Write a concise executive summary of marketing intelligence for {org_name}. "
        "Cover ICP signals, top pains, objections, and one recommended next action.",
        context,
    )
    if summary is None:
        logger.error(
            "Executive summary generation failed for org %s: LLM produced no answer", org_id
        )
        return {"summary": None, "citations": []}
    return {"summary": summary, "citations": [c["ref"] for c in context[:8]]}
