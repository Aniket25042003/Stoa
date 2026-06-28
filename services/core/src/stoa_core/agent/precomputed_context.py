"""Assemble precomputed insight + structured CRM context for fast agent synthesis."""

from __future__ import annotations

import json
import logging
from typing import Any

from stoa_core.agent.tools.registry import AGENT_MEMORY_KINDS
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.intelligence.structured import aggregate_crm_stats
from stoa_core.llm.router import invoke_text
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

ENRICHED_ANSWER_SYSTEM = """You are a marketing intelligence analyst for Stoa.
Answer using the precomputed insight, CRM statistics, and supplemental context provided.
Adapt the precomputed answer to the user's exact question and conversation tone.
Do not include inline citation markers or bracketed source IDs in the answer.
Be concise and actionable. Do not invent facts not supported by the provided data."""


def load_matched_insight(
    org_id: str,
    key: str,
    scope: str = "intelligence",
) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("key, title, scope, content, citations, is_stale, created_at")
        .eq("org_id", org_id)
        .eq("scope", scope)
        .eq("key", key)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows and isinstance(rows[0], dict) else None


def build_crm_stats_context(org_id: str) -> dict[str, Any]:
    return aggregate_crm_stats(org_id)


def _context_item(ref: str, text: str, title: str = "") -> dict[str, Any]:
    return {"ref": ref, "text": text, "title": title or ref}


def build_enriched_context(
    org_id: str,
    insight: dict[str, Any],
    question: str,
    *,
    light_retrieval_k: int = 4,
    skip_retrieval: bool = False,
) -> list[dict[str, Any]]:
    """Build context blocks: precomputed insight + CRM stats + optional light RAG."""
    blocks: list[dict[str, Any]] = []

    content = insight.get("content") or {}
    answer = ""
    if isinstance(content, dict):
        answer = str(content.get("answer") or "")
    if answer:
        blocks.append(
            _context_item(
                f"precomputed:{insight.get('key')}",
                f"Precomputed insight ({insight.get('title')}):\n{answer}",
                str(insight.get("title") or "Precomputed insight"),
            )
        )

    stats = build_crm_stats_context(org_id)
    blocks.append(
        _context_item(
            "crm:aggregate_stats",
            "CRM aggregate statistics:\n" + json.dumps(stats, default=str),
            "CRM statistics",
        )
    )

    if not skip_retrieval:
        try:
            extra = retrieve_context(
                org_id,
                question,
                kinds=AGENT_MEMORY_KINDS,
                k=light_retrieval_k,
            )
            blocks.extend(extra[:light_retrieval_k])
        except Exception as exc:
            logger.debug("Light retrieval skipped for enriched context: %s", exc)

    return blocks


def build_structured_rag_prefix(org_id: str, question: str) -> list[dict[str, Any]]:
    """Inject CRM stats for single-domain questions without a precomputed match."""
    if not _mentions_crm_domain(question):
        return []
    stats = build_crm_stats_context(org_id)
    return [
        _context_item(
            "crm:aggregate_stats",
            "CRM aggregate statistics:\n" + json.dumps(stats, default=str),
            "CRM statistics",
        )
    ]


def _mentions_crm_domain(question: str) -> bool:
    lowered = question.lower()
    markers = (
        "icp",
        "segment",
        "customer",
        "deal",
        "win rate",
        "converting",
        "conversion",
        "pipeline",
        "crm",
        "account",
    )
    return any(m in lowered for m in markers)


def synthesize_from_enriched_context(
    question: str,
    context: list[dict[str, Any]],
    *,
    history_snippets: list[str] | None = None,
) -> str:
    lines = []
    for item in context[:30]:
        ref = item.get("ref", "unknown")
        text = item.get("text", "")
        lines.append(f"[{ref}] {text}")

    history_block = ""
    if history_snippets:
        history_block = "\n\nRecent conversation:\n" + "\n".join(history_snippets[:4])

    user = f"Question: {question}{history_block}\n\nContext:\n" + "\n".join(lines)
    answer, _provider = invoke_text(ENRICHED_ANSWER_SYSTEM, user, task_name="synthesize")
    return answer or "Unable to generate an answer right now. Please try again."
