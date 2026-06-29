"""Org-aware multi-tier agent route resolution."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Literal

from stoa_core.agent.route import classify_agent_route, requires_tools_route
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.insights.common import COMMON_QUESTIONS
from stoa_core.llm.router import invoke_json

logger = logging.getLogger(__name__)

AgentRoute = Literal[
    "precomputed_enriched",
    "rag_only",
    "tools_bounded",
    "tools_react",
]

INSIGHT_SCOPES = ("intelligence", "campaign_analysis", "alignment")

HIGH_CONFIDENCE = 0.75
BORDERLINE_LOW = 0.5

_ICP_DOMAIN_RE = re.compile(
    r"\b(icp|segment|converting|conversion|win\s*rate|deal\s*size|customer\s*profile|"
    r"pain\s*point|objection|buying\s*trigger|win/loss|prioriti[sz]e)\b",
    re.IGNORECASE,
)

_ROUTE_SYSTEM = """Classify the best execution path for a GTM assistant question.

Return JSON:
{
  "route": "precomputed_enriched" | "rag_only" | "tools_bounded",
  "reason": "short explanation"
}

Use "precomputed_enriched" when the question closely matches an available precomputed insight
key and is single-domain (ICP, objections, pain points, win/loss).

Use "tools_bounded" when the user needs cross-feature comparison, live connector data,
refresh/sync, competitive+campaign synthesis, or multi-dashboard orchestration.

Use "rag_only" for other straightforward factual questions answerable from documents/CRM."""

_NON_WORD_RE = re.compile(r"[^\w\s]+")


def _normalize_text(text: str) -> str:
    lowered = _NON_WORD_RE.sub(" ", text.lower())
    return " ".join(lowered.split())


def _token_set(text: str) -> set[str]:
    return {t for t in _normalize_text(text).split() if len(t) > 2}


def jaccard_similarity(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass(frozen=True)
class RouteDecision:
    route: AgentRoute
    reason: str
    matched_insight_key: str | None = None
    matched_scope: str | None = None
    confidence: float = 0.0
    insight_is_stale: bool = False


def _load_org_insights(org_id: str) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("key, title, scope, content, is_stale, citations")
        .eq("org_id", org_id)
        .in_("scope", list(INSIGHT_SCOPES))
        .execute()
    )
    return [r for r in (res.data or []) if isinstance(r, dict)]


def _canonical_templates() -> dict[str, dict[str, str]]:
    templates: dict[str, dict[str, str]] = {}
    for item in COMMON_QUESTIONS:
        templates[item["key"]] = {
            "title": item["title"],
            "question": item["question"],
            "scope": "intelligence",
        }
    return templates


def _match_precomputed_insight(
    org_id: str,
    question: str,
) -> tuple[dict[str, Any] | None, float]:
    insights = _load_org_insights(org_id)
    if not insights:
        return None, 0.0

    templates = _canonical_templates()
    best: dict[str, Any] | None = None
    best_score = 0.0

    for row in insights:
        key = str(row.get("key") or "")
        title = str(row.get("title") or "")
        template = templates.get(key, {})
        template_q = template.get("question", "")
        template_title = template.get("title", title)

        scores = [
            jaccard_similarity(question, template_q),
            jaccard_similarity(question, template_title),
            jaccard_similarity(question, title),
            jaccard_similarity(question, key.replace("_", " ")),
        ]
        if _normalize_text(question) == _normalize_text(template_q):
            scores.append(1.0)
        score = max(scores)
        if score > best_score:
            best_score = score
            best = row

    if best is None or best_score < BORDERLINE_LOW:
        return None, best_score

    if BORDERLINE_LOW <= best_score < HIGH_CONFIDENCE:
        try:
            from stoa_core.ingestion.embed import embed_query

            q_vec = embed_query(question)
            key = str(best.get("key") or "")
            template = templates.get(key, {})
            ref_text = template.get("question") or str(best.get("title") or "")
            ref_vec = embed_query(ref_text)
            embed_score = _cosine_similarity(q_vec, ref_vec)
            best_score = max(best_score, embed_score)
        except Exception as exc:
            logger.debug("Embedding match skipped: %s", exc)

    return best, best_score


def resolve_agent_route(
    org_id: str,
    question: str,
    *,
    history: list[dict[str, Any]] | None = None,
) -> RouteDecision:
    """Resolve org-aware execution tier for a user question."""
    q = question.strip()
    if not q:
        return RouteDecision(route="rag_only", reason="empty_question")

    if requires_tools_route(q):
        return RouteDecision(route="tools_bounded", reason="hard_tools_signal")

    matched, confidence = _match_precomputed_insight(org_id, q)
    if matched and confidence >= HIGH_CONFIDENCE:
        is_stale = bool(matched.get("is_stale"))
        if is_stale:
            return RouteDecision(
                route="rag_only",
                reason="precomputed_insight_stale",
                matched_insight_key=str(matched.get("key") or ""),
                matched_scope=str(matched.get("scope") or ""),
                confidence=confidence,
                insight_is_stale=True,
            )
        return RouteDecision(
            route="precomputed_enriched",
            reason="precomputed_insight_match",
            matched_insight_key=str(matched.get("key") or ""),
            matched_scope=str(matched.get("scope") or "intelligence"),
            confidence=confidence,
        )

    if matched and confidence >= BORDERLINE_LOW and _ICP_DOMAIN_RE.search(q):
        is_stale = bool(matched.get("is_stale"))
        if not is_stale:
            return RouteDecision(
                route="precomputed_enriched",
                reason="domain_heuristic_with_insight",
                matched_insight_key=str(matched.get("key") or ""),
                matched_scope=str(matched.get("scope") or "intelligence"),
                confidence=confidence,
            )

    history = history or []
    snippets = [
        f"{row.get('role', 'user')}: {str(row.get('content') or '')[:180]}"
        for row in history[-4:]
        if row.get("content")
    ]
    insight_keys = [str(r.get("key") or "") for r in _load_org_insights(org_id) if r.get("key")]

    parsed, _provider = invoke_json(
        _ROUTE_SYSTEM,
        {
            "question": q,
            "recent_messages": snippets,
            "available_precomputed_keys": insight_keys[:20],
        },
        task_name="needs_tools",
    )
    if parsed:
        llm_route = str(parsed.get("route") or "")
        reason = str(parsed.get("reason") or "llm_classifier")
        if llm_route == "precomputed_enriched" and matched and not matched.get("is_stale"):
            return RouteDecision(
                route="precomputed_enriched",
                reason=reason,
                matched_insight_key=str(matched.get("key") or ""),
                matched_scope=str(matched.get("scope") or "intelligence"),
                confidence=confidence,
            )
        if llm_route == "tools_bounded":
            return RouteDecision(route="tools_bounded", reason=reason)
        if llm_route in {"rag_only", "precomputed_enriched"}:
            return RouteDecision(route="rag_only", reason=reason)

    legacy = classify_agent_route(q, history=history)
    if legacy == "tools":
        return RouteDecision(route="tools_bounded", reason="legacy_classifier_tools")
    return RouteDecision(route="rag_only", reason="default_rag_only")
