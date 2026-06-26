"""Org-specific proactive insight generation."""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.llm.router import invoke_json
from stoa_core.rag.answer import try_answer_question
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

DYNAMIC_KINDS = [
    "company_profile",
    "company_web_research",
    "competitive_snapshot",
    "icp_profile",
]


def generate_dynamic_insights_for_org(org_id: str) -> dict[str, Any]:
    sb = get_supabase_admin()
    org_res = sb.table("organizations").select("name").eq("id", org_id).limit(1).execute()
    org_name = (org_res.data or [{}])[0].get("name") or "your company"

    schema = '{"questions": [{"key": "...", "title": "...", "question": "..."}]}'
    parsed, _ = invoke_json(
        "Generate 2-3 marketing intelligence questions specific to this company. Return JSON: " + schema,
        {"company": org_name},
        task_name="summarize",
    )
    questions = (parsed or {}).get("questions") or [
        {
            "key": "competitive_positioning",
            "title": "How should we position against competitors?",
            "question": f"How should {org_name} position against key competitors based on available evidence?",
        },
        {
            "key": "icp_gaps",
            "title": "What ICP gaps should we address?",
            "question": f"What gaps exist in {org_name}'s ideal customer profile based on current data?",
        },
    ]

    generated = 0
    for q in questions[:3]:
        key = str(q.get("key") or "dynamic")[:80]
        title = str(q.get("title") or key)[:200]
        question = str(q.get("question") or "")[:2000]
        if not question:
            continue
        context = retrieve_context(org_id, question, kinds=DYNAMIC_KINDS)
        answer = try_answer_question(question, context)
        if not answer:
            continue
        sb.table("precomputed_insights").upsert(
            {
                "org_id": org_id,
                "scope": "intelligence",
                "key": key,
                "title": title,
                "content": {"answer": answer},
                "citations": [c["ref"] for c in context[:8]],
                "is_stale": False,
                "source_document_count": 0,
            },
            on_conflict="org_id,scope,key",
        ).execute()
        generated += 1

    return {"generated": generated}
