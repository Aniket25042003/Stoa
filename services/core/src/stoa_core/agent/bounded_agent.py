"""Bounded plan-execute-synthesize agent path (fixed LLM call budget)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from stoa_core.agent.progress import format_tool_label
from stoa_core.agent.tools.registry import TOOL_CATALOG, build_agent_tools
from stoa_core.config import get_settings
from stoa_core.llm.content import extract_text_content
from stoa_core.llm.router import invoke_json, invoke_text

logger = logging.getLogger(__name__)

PLAN_SYSTEM = """You are a GTM agent planner. Select the minimum tools needed to answer \
the question.

Return JSON:
{
  "tools": [{"name": "<tool_name>", "args": {<args dict>}}],
  "needs_live_search": false,
  "reason": "why these tools"
}

Rules:
- Select at most 3 tools.
- Prefer dashboard tools for ICP, campaigns, competitive, alignment questions.
- Use search_connected_sources only when needs_live_search is true or user asks for
  live/latest data.
- Do NOT select search_workspace_memory when retrieved_context_count >= 6 unless the user asks for
  a clearly different topic.
- Use refresh_* tools only when user explicitly asks to refresh or sync.

Available tools:
"""

SYNTHESIZE_SYSTEM = """You are Stoa's unified GTM Agent. Synthesize a clear, actionable answer \
from tool results and retrieved context. Do not include inline citation markers or source IDs \
in the answer.
Do not invent metrics."""


@dataclass
class BoundedAgentResult:
    answer: str
    used_tools: list[str]
    tool_events: list[dict[str, Any]]
    route: str = "tools_bounded"
    plan_reason: str = ""


def _tool_map(tools: list[Any]) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for tool in tools:
        name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if name:
            mapping[str(name)] = tool
    return mapping


def _catalog_text() -> str:
    lines = []
    for name, meta in TOOL_CATALOG.items():
        lines.append(f"- {name}: {meta.get('description', '')} When: {meta.get('when', '')}")
    return "\n".join(lines)


def _should_block_memory_search(question: str, context_count: int, planned: list[dict]) -> bool:
    if context_count < 6:
        return False
    return any(str(t.get("name")) == "search_workspace_memory" for t in planned)


def _execute_tool(tool: Any, args: dict[str, Any]) -> str:
    if hasattr(tool, "invoke"):
        return str(tool.invoke(args))
    if callable(tool):
        return str(tool(**args))
    return json.dumps({"error": "tool not callable"})


def plan_tools(
    question: str,
    *,
    context_count: int,
    context_preview: str,
) -> dict[str, Any] | None:
    payload = {
        "question": question,
        "retrieved_context_count": context_count,
        "context_preview": context_preview[:2000],
    }
    parsed, _ = invoke_json(
        PLAN_SYSTEM + _catalog_text(),
        payload,
        task_name="needs_tools",
    )
    return parsed if isinstance(parsed, dict) else None


def run_bounded_agent_turn(
    org_id: str,
    conversation_id: str,
    question: str,
    long_term_context: list[dict[str, Any]],
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> BoundedAgentResult:
    settings = get_settings()
    max_tools = settings.agent_max_tools_per_turn

    def _progress(payload: dict[str, Any]) -> None:
        if on_progress:
            on_progress(payload)

    _progress({"status": "thinking", "message": "Planning tool strategy…"})
    context_preview = "\n".join(
        f"[{c.get('ref')}] {str(c.get('text', ''))[:200]}" for c in long_term_context[:6]
    )
    plan = plan_tools(
        question,
        context_count=len(long_term_context),
        context_preview=context_preview,
    )

    if not plan or not isinstance(plan.get("tools"), list):
        raise ValueError("Tool plan unavailable")

    planned_tools: list[dict[str, Any]] = list(plan.get("tools") or [])[:max_tools]
    if _should_block_memory_search(question, len(long_term_context), planned_tools):
        planned_tools = [
            t for t in planned_tools if str(t.get("name")) != "search_workspace_memory"
        ]

    tools = build_agent_tools(org_id, conversation_id)
    by_name = _tool_map(tools)

    used_tools: list[str] = []
    tool_events: list[dict[str, Any]] = []
    tool_results: list[dict[str, Any]] = []

    def _run_one(spec: dict[str, Any]) -> dict[str, Any]:
        name = str(spec.get("name") or "")
        args = spec.get("args") if isinstance(spec.get("args"), dict) else {}
        tool = by_name.get(name)
        if tool is None:
            return {"tool": name, "error": "unknown tool", "output": ""}
        label = format_tool_label(name)
        _progress({"status": "tool_call", "tool": name, "message": f"Calling {label}…"})
        try:
            output = _execute_tool(tool, args)
        except Exception as exc:
            output = json.dumps({"error": str(exc)})
        _progress(
            {
                "status": "tool_done",
                "tool": name,
                "message": f"{label.capitalize()} complete",
            }
        )
        return {"tool": name, "output": output}

    with ThreadPoolExecutor(max_workers=min(3, len(planned_tools) or 1)) as pool:
        futures = {pool.submit(_run_one, spec): spec for spec in planned_tools}
        for future in as_completed(futures):
            result = future.result()
            name = str(result.get("tool") or "")
            if name and name not in used_tools:
                used_tools.append(name)
            tool_events.append(
                {
                    "tool": name,
                    "observation_preview": str(result.get("output") or "")[:400],
                }
            )
            tool_results.append(result)

    if used_tools:
        _progress({"status": "tool_summary", "used_tools": list(used_tools)})

    _progress({"status": "thinking", "message": "Synthesizing answer…"})
    synth_user = (
        f"Question: {question}\n\n"
        f"Retrieved context:\n{context_preview}\n\n"
        f"Tool results:\n{json.dumps(tool_results, default=str)[:12000]}"
    )
    answer, _ = invoke_text(SYNTHESIZE_SYSTEM, synth_user, task_name="synthesize")
    clean = extract_text_content(answer).strip() or "I couldn't generate a response right now."

    return BoundedAgentResult(
        answer=clean,
        used_tools=used_tools,
        tool_events=tool_events,
        plan_reason=str(plan.get("reason") or ""),
    )
