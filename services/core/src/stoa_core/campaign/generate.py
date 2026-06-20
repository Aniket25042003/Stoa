"""
File: services/core/src/stoa_core/campaign/generate.py
Layer: Core Campaign Generation
Purpose: Implements generate behavior for the core campaign generation.
Dependencies: stoa_core
"""


from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_json

CAMPAIGN_SYSTEM = """Generate a campaign asset package grounded in ICP and competitive context.
Return JSON:
{
  "messaging": {"headline": "...", "value_prop": "...", "proof_points": []},
  "landing_page": {"hero": "...", "sections": [{"title": "...", "body": "..."}]},
  "emails": [{"subject": "...", "body": "..."}],
  "social": [{"channel": "linkedin|x", "text": "..."}],
  "battlecard": {"objections": [], "differentiators": [], "talk_track": "..."}
}
Match brand voice if provided. Be specific, not generic."""


def generate_campaign_assets(
    brief: str,
    icp_context: dict[str, Any] | None,
    competitive_context: list[dict[str, Any]] | None,
    brand_voice: str | None = None,
    knowledge_context: str | None = None,
) -> dict[str, Any] | None:
    """Handles generate campaign assets logic for the surrounding Stoa workflow.

    Args:
        brief (str): Input value used by this workflow step.
        icp_context (dict[str, Any] | None): Input value used by this workflow step.
        competitive_context (list[dict[str, Any]] | None): Input value used by this workflow step.
        brand_voice (str | None): Input value used by this workflow step.
        knowledge_context (str | None): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    payload = {
        "brief": brief,
        "icp": icp_context or {},
        "competitive": competitive_context or [],
        "brand_voice": brand_voice or "professional, clear, evidence-backed",
        "knowledge_base_context": knowledge_context or "",
    }
    parsed, _ = invoke_json(CAMPAIGN_SYSTEM, payload, task_name="campaign_plan")
    return parsed
