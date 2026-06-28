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

TOOL_CATALOG: dict[str, dict[str, str]] = {
    "search_workspace_memory": {
        "description": "Additional KB vector search mid-turn.",
        "when": "Topic differs from initial retrieval or context is thin.",
    },
    "get_workspace_freshness": {
        "description": "Sync times, stale insights, KB version.",
        "when": "User asks if data is current or stale.",
    },
    "search_connected_sources": {
        "description": "Live connector search (HubSpot, Salesforce, etc.).",
        "when": "User needs live/latest external data.",
    },
    "lookup_canonical_records": {
        "description": "Exact CRM entity lookup by name or ID.",
        "when": "User names a specific account, deal, or contact.",
    },
    "refresh_connected_source": {
        "description": "Queue background connector sync.",
        "when": "User explicitly asks to refresh or sync a source.",
    },
    "refresh_precomputed_insights": {
        "description": "Queue insight precompute refresh.",
        "when": "User asks to refresh prepared insights.",
    },
    "refresh_competitor_intel": {
        "description": "Queue competitive intel refresh.",
        "when": "User asks to refresh competitor research.",
    },
    "search_public_web": {
        "description": "Guardrailed public web search.",
        "when": "External public information is required.",
    },
    "icp_customer_research_tool": {
        "description": "ICP segments, win rates, CRM highlights.",
        "when": "Customer segments, conversion, ICP, or deal performance.",
    },
    "content_bottleneck_tool": {
        "description": "Content production throughput and failures.",
        "when": "Content pipeline bottlenecks or asset generation issues.",
    },
    "competitive_intelligence_tool": {
        "description": "Competitive snapshots and alerts.",
        "when": "Competitor positioning or competitive changes.",
    },
    "launch_orchestration_tool": {
        "description": "Launch planning across campaigns and content.",
        "when": "Product/campaign launch orchestration.",
    },
    "campaign_analysis_tool": {
        "description": "Campaign performance and metrics.",
        "when": "Campaign ROI, channel performance, or campaign analysis.",
    },
    "sales_marketing_alignment_tool": {
        "description": "Sales vs marketing alignment friction.",
        "when": "Pipeline alignment, messaging gaps, or SLA friction.",
    },
}


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
