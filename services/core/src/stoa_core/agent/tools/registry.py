"""Agent tool registry — composes all tiers for the unified GTM agent."""

from __future__ import annotations

from typing import Any

from stoa_core.agent.tools.crm import build_crm_tools
from stoa_core.agent.tools.dashboard import build_dashboard_tools
from stoa_core.agent.tools.insights import build_insights_tools
from stoa_core.agent.tools.integrations import build_integration_tools
from stoa_core.agent.tools.memory import build_memory_tools
from stoa_core.agent.tools.web import build_web_tools

CONVERSATION_MEMORY_KIND = "conversation_memory"
AGENT_SEARCH_EVIDENCE_KIND = "agent_search_evidence"

AGENT_MEMORY_KINDS = [
    "document",
    "company_profile",
    "icp_profile",
    "crm_account",
    "crm_contact",
    "crm_deal",
    "call_transcript",
    "support_ticket",
    "review",
    "product_analytics_summary",
    "competitive_snapshot",
    "campaign_asset",
    "campaign_metrics",
    "content_asset",
    CONVERSATION_MEMORY_KIND,
    AGENT_SEARCH_EVIDENCE_KIND,
]


def build_agent_tools(
    org_id: str,
    conversation_id: str,
    *,
    include_web: bool = True,
) -> list[Any]:
    tools: list[Any] = []
    tools.extend(build_memory_tools(org_id, conversation_id, memory_kinds=AGENT_MEMORY_KINDS))
    tools.extend(build_integration_tools(org_id, conversation_id))
    tools.extend(build_insights_tools(org_id))
    tools.extend(build_crm_tools(org_id, conversation_id))
    tools.extend(build_dashboard_tools(org_id))
    if include_web:
        tools.extend(build_web_tools(org_id, conversation_id))
    return tools
