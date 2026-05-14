from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

import operator


class ResearchItem(TypedDict, total=False):
    source_url: str
    source_type: Literal["web", "serp", "crawl", "other"]
    query: str
    title: str
    raw_excerpt: str
    summary: str
    sentiment: str | None
    confidence: float | None
    retrieved_at: str
    metadata: dict[str, Any]


class GTMState(TypedDict, total=False):
    run_id: str
    user_id: str
    input: dict[str, Any]
    progress_callback: Any
    research_items_callback: Any
    master_plan: dict[str, Any]
    agent_plans: dict[str, Any]
    approvals: dict[str, Any]
    memory_context: list[dict[str, Any]]
    research_plan: dict[str, Any]
    research_items: Annotated[list[ResearchItem], operator.add]
    research_bundle: dict[str, Any]
    tool_results: list[dict[str, Any]]
    tool_errors: Annotated[list[str], operator.add]
    segmentation: dict[str, Any]
    positioning: dict[str, Any]
    channels: dict[str, Any]
    validation: dict[str, Any]
    final_markdown: str
    errors: Annotated[list[str], operator.add]
