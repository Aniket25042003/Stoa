"""Agent turn progress events for SSE transparency."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

TOOL_LABELS: dict[str, str] = {
    "search_workspace_memory": "workspace memory",
    "get_workspace_freshness": "data freshness",
    "search_connected_sources": "connected sources",
    "lookup_canonical_records": "CRM records",
    "refresh_connected_source": "source refresh",
    "refresh_precomputed_insights": "insight refresh",
    "refresh_competitor_intel": "competitive refresh",
    "search_public_web": "web search",
    "icp_customer_research_tool": "ICP research",
    "content_bottleneck_tool": "content analysis",
    "competitive_intelligence_tool": "competitive intel",
    "launch_orchestration_tool": "launch planning",
    "campaign_analysis_tool": "campaign analysis",
    "sales_marketing_alignment_tool": "sales & marketing alignment",
}


def format_tool_label(tool_name: str) -> str:
    """Return a short human label for an agent tool name."""
    key = (tool_name or "").strip()
    if not key:
        return "tool"
    if key in TOOL_LABELS:
        return TOOL_LABELS[key]
    return key.replace("_", " ").strip()


class AgentProgressCallback(BaseCallbackHandler):
    """Publishes tool-call progress while the LangChain agent runs."""

    def __init__(self, on_progress: Callable[[dict[str, Any]], None]) -> None:
        self._on_progress = on_progress
        self.used_tools: list[str] = []
        self._current_tool: str | None = None
        self._tool_starts = 0
        self._llm_starts = 0

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = str(serialized.get("name") or "tool")
        self._current_tool = name
        self._tool_starts += 1
        label = format_tool_label(name)
        self._on_progress(
            {
                "status": "tool_call",
                "tool": name,
                "message": f"Calling {label}…",
            }
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = self._current_tool or "tool"
        if name not in self.used_tools:
            self.used_tools.append(name)
        label = format_tool_label(name)
        self._on_progress(
            {
                "status": "tool_done",
                "tool": name,
                "message": f"{label.capitalize()} complete",
            }
        )
        self._on_progress(
            {
                "status": "tool_summary",
                "used_tools": list(self.used_tools),
            }
        )
        self._current_tool = None

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        self._llm_starts += 1
        if self.used_tools and self._llm_starts > self._tool_starts:
            self._on_progress(
                {
                    "status": "thinking",
                    "message": "Synthesizing answer…",
                }
            )
