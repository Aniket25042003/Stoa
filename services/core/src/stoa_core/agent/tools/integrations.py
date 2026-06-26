"""Tier 2 agent tool: live connector search with evidence pipeline."""

from __future__ import annotations

import hashlib
import json
import logging

from langchain_core.tools import StructuredTool

from stoa_core.agent.evidence import (
    get_cached_evidence,
    hits_to_tool_json,
    store_conversation_evidence,
)
from stoa_core.agent.rate_limit import check_live_search_limit
from stoa_core.integrations.agent_search import run_agent_search

logger = logging.getLogger(__name__)


def build_integration_tools(org_id: str, conversation_id: str) -> list[StructuredTool]:
    def search_connected_sources(
        provider: str,
        query: str,
        entity_type: str | None = None,
    ) -> str:
        """Query live external systems when workspace memory is insufficient or outdated."""
        provider = provider.strip().lower()
        if not check_live_search_limit(org_id):
            return json.dumps(
                {
                    "error": "Live search rate limit exceeded for this hour",
                    "suggestion": "Use search_workspace_memory or wait before retrying",
                }
            )

        cached = get_cached_evidence(
            org_id,
            conversation_id,
            source=provider,
            query=query,
            entity_type=entity_type,
        )
        if cached is not None:
            logger.info(
                "agent_search_cache_hit org=%s provider=%s qhash=%s",
                org_id,
                provider,
                hashlib.sha256(query.encode()).hexdigest()[:12],
            )
            return hits_to_tool_json(cached, cached=True)

        hits, err = run_agent_search(org_id, provider, query, entity_type=entity_type)
        if err:
            return json.dumps(
                {
                    "error": err,
                    "suggestion": "Try refresh_connected_source or check get_workspace_freshness",
                }
            )
        if not hits:
            return json.dumps(
                {
                    "count": 0,
                    "hits": [],
                    "suggestion": "No live results — consider refresh_connected_source",
                }
            )

        stored = store_conversation_evidence(
            org_id,
            conversation_id,
            source=provider,
            query=query,
            hits=hits,
            entity_type=entity_type,
        )
        logger.info(
            "agent_live_search org=%s provider=%s hits=%d qhash=%s",
            org_id,
            provider,
            len(stored),
            hashlib.sha256(query.encode()).hexdigest()[:12],
        )
        return hits_to_tool_json(stored, cached=False)

    return [StructuredTool.from_function(search_connected_sources)]
