"""Tier 5 agent tool: guardrailed public web research."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from langchain_core.tools import StructuredTool

from stoa_core.agent.evidence import EvidenceHit, store_conversation_evidence
from stoa_core.agent.rate_limit import check_web_search_limit
from stoa_core.config import get_settings
from stoa_core.research.web import research_web


def build_web_tools(org_id: str, conversation_id: str) -> list[StructuredTool]:
    def search_public_web(query: str) -> str:
        """Search the public web when workspace memory and connectors lack data."""
        settings = get_settings()
        if settings.disable_external_research:
            return json.dumps({"error": "External web research is disabled for this workspace"})

        if not check_web_search_limit(org_id):
            return json.dumps({"error": "Daily web search limit exceeded for this workspace"})

        result = research_web(query, max_results=6)
        now = datetime.now(UTC).isoformat()
        hits: list[EvidenceHit] = []
        for idx, item in enumerate(result.items):
            hits.append(
                EvidenceHit(
                    id=f"web-{idx}",
                    title=item.title or item.source_url or f"Result {idx}",
                    snippet=item.summary or item.raw_excerpt or "",
                    uri=item.source_url or f"web:{idx}",
                    provider="web",
                    source="web",
                    fetched_at=now,
                )
            )
        stored = store_conversation_evidence(
            org_id,
            conversation_id,
            source="web",
            query=query,
            hits=hits,
        )
        return json.dumps(
            {
                "source_type": result.source_type,
                "count": len(stored),
                "hits": [
                    {"title": h.title, "snippet": h.snippet[:300], "uri": h.uri}
                    for h in stored
                ],
            },
            default=str,
        )

    return [StructuredTool.from_function(search_public_web)]
