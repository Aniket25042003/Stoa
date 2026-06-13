"""ICP profile synthesis from aggregated intelligence signals."""

from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_json

ICP_SYSTEM = """You synthesize an evidence-backed ICP profile from customer intelligence signals.
Return JSON:
{
  "summary": "...",
  "top_segments": [{"name": "...", "traits": [], "evidence_ids": []}],
  "top_pain_points": [{"text": "...", "frequency": "high|medium|low", "evidence_ids": []}],
  "top_objections": [{"text": "...", "evidence_ids": []}],
  "buying_triggers": [{"text": "...", "evidence_ids": []}],
  "win_loss_themes": [{"theme": "...", "type": "win|loss", "evidence_ids": []}]
}
Be conservative. Only claim what the evidence supports."""


def build_icp_profile(
    signals: list[dict[str, Any]],
    *,
    structured_stats: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not signals and not structured_stats:
        return None
    payload: dict[str, Any] = {
        "signals": [
            {
                "id": s.get("id"),
                "kind": s.get("kind"),
                "content": s.get("content"),
                "confidence": s.get("confidence"),
            }
            for s in signals[:200]
        ],
    }
    if structured_stats:
        payload["crm_aggregates"] = structured_stats
    parsed, _provider = invoke_json(ICP_SYSTEM, payload, task_name="icp_build")
    if parsed and structured_stats:
        parsed["structured_crm"] = structured_stats
    return parsed
