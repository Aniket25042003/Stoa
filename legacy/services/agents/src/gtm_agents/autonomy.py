from __future__ import annotations

import os
import re
import time
from typing import Any

from gtm_agents.llm import invoke_json, load_config
from gtm_agents.memory import append_memory, read_memory, write_context_snapshot
from gtm_agents.mcp_client import call_research_tools, list_research_tools
from gtm_agents.observability import span
from gtm_agents.state import ResearchItem
from gtm_agents.tools.research import merge_research


def _llm_json(system: str, payload: dict[str, Any], max_chars: int = 16000, task_tier: str = "standard") -> dict[str, Any] | None:
    if os.getenv("GTM_DISABLE_LLM") == "true":
        return None
    cfg = load_config()
    payload_keys = list(payload.keys()) if isinstance(payload, dict) else []
    with span(
        "llm_json",
        "llm",
        {
            "primary_provider": cfg.primary,
            "auto_failover": cfg.auto_failover,
            "vertex_model": cfg.vertex_model,
            "vertex_model_fast": cfg.vertex_model_fast,
            "vertex_model_pro": cfg.vertex_model_pro,
            "openai_model": cfg.openai_model,
            "task_tier": task_tier,
            "system_preview": (system[:400] + "…") if len(system) > 400 else system,
            "payload_keys": payload_keys,
            "max_chars": max_chars,
        },
    ):
        parsed, provider_used = invoke_json(system, payload, max_chars=max_chars, config=cfg, task_tier=task_tier)  # type: ignore[arg-type]
        if provider_used and provider_used != cfg.primary:
            # Surface failover events into the trace so operators see when Vertex went down.
            with span(
                "llm_failover",
                "llm",
                {"primary": cfg.primary, "fallback_used": provider_used},
            ):
                pass
        return parsed


def _product_context(user_input: dict[str, Any]) -> str:
    fields = [
        ("Product", user_input.get("product_name")),
        ("Description", user_input.get("product_description")),
        ("Website", user_input.get("website_url")),
        ("Target customers", user_input.get("target_customers")),
        ("Geography", user_input.get("geography")),
        ("Business model", user_input.get("business_model")),
        ("Stage", user_input.get("stage")),
        ("Known competitors", user_input.get("known_competitors")),
        ("Constraints", user_input.get("constraints")),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _safe_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    parsed = _safe_int(value, default)
    return max(minimum, min(parsed, maximum))


def _normalize_steps(plan: dict[str, Any], fallback_steps: list[str]) -> dict[str, Any]:
    raw_steps = plan.get("steps") if isinstance(plan.get("steps"), list) else []
    steps = []
    for i, step in enumerate(raw_steps or fallback_steps, start=1):
        if isinstance(step, dict):
            description = str(step.get("description") or step.get("task") or step)
        else:
            description = str(step)
        steps.append({"id": f"step_{i}", "description": description, "status": "pending", "review": None})
    return {**plan, "steps": steps, "status": "planned"}


def create_agent_plan(
    agent_name: str,
    objective: str,
    context: dict[str, Any],
    fallback_steps: list[str],
    run_id: str | None = None,
    parent_agent: str | None = None,
) -> dict[str, Any]:
    with span(
        "create_agent_plan",
        "chain",
        {"agent_name": agent_name, "parent_agent": parent_agent, "run_id": run_id, "objective_preview": (objective[:240] + "…") if len(objective) > 240 else objective},
    ):
        return _create_agent_plan_impl(agent_name, objective, context, fallback_steps, run_id, parent_agent)


def _create_agent_plan_impl(
    agent_name: str,
    objective: str,
    context: dict[str, Any],
    fallback_steps: list[str],
    run_id: str | None = None,
    parent_agent: str | None = None,
) -> dict[str, Any]:
    prompt = f"""You are {agent_name} in a hierarchical autonomous GTM agent system.
Your parent agent is {parent_agent or "none"}.
Create a concrete step-by-step plan before doing work.
Each step should be independently checkable. Include completion criteria and likely risks.
Return JSON with: objective, assumptions, steps, approval_criteria, stop_conditions, continue_conditions."""
    planned = _llm_json(prompt, {"objective": objective, "context": context, "shared_memory": read_memory(run_id, 30)}, task_tier="cheap")
    if not planned:
        planned = {
            "objective": objective,
            "assumptions": ["LLM planning model not configured; using deterministic execution plan."],
            "approval_criteria": ["Output exists", "Known warnings are documented", "No critical validation failures"],
            "stop_conditions": ["All planned steps complete and parent approval is granted"],
            "continue_conditions": ["Critical review issue found", "Required evidence/output missing"],
        }
    normalized = _normalize_steps(planned, fallback_steps)
    append_memory(run_id, agent_name, "plan_created", {"parent_agent": parent_agent, "plan": normalized})
    return normalized


def create_master_plan_for_user(
    user_input: dict[str, Any],
    user_feedback: str | None = None,
    prior_plan: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    context = {"founder_input": user_input, "prior_plan": prior_plan or {}, "user_feedback": user_feedback}
    plan = create_agent_plan(
        "main_agent",
        "Create the full GTM agent execution plan for user approval before any research, reasoning, or writing begins.",
        context,
        [
            "Confirm product details and GTM success criteria from the user input.",
            "Define research-layer goals, available MCP tool policy, evidence quality bar, and approval criteria.",
            "Define reasoning-layer goals, expected parent/subagent responsibilities, and approval criteria.",
            "Define writing-layer goals, report quality bar, citation requirements, and approval criteria.",
            "Define main-agent final review criteria and loop rules for rejected layer work.",
            "Wait for user approval or requested edits before execution.",
        ],
        run_id,
        "user",
    )
    plan["requires_user_approval"] = True
    plan["user_feedback_applied"] = user_feedback or None
    if user_feedback:
        plan.setdefault("user_requested_edits", []).append(user_feedback)
        plan.setdefault("steps", []).append(
            {
                "id": f"user_edit_{len(plan.get('steps') or []) + 1}",
                "description": f"Apply user-requested plan update before execution: {user_feedback}",
                "status": "pending",
                "review": "Awaiting user approval of regenerated plan.",
            }
        )
    plan["hierarchy"] = {
        "top_boss": "user",
        "executor": "main_agent",
        "layer_parents": ["research_parent_agent", "reasoning_parent_agent", "writing_parent_agent"],
        "rule": "No execution begins until the user approves this master plan.",
    }
    return plan


def complete_step(plan: dict[str, Any], step_index: int, review: str | None = None) -> None:
    steps = plan.get("steps") or []
    if 0 <= step_index < len(steps):
        steps[step_index]["status"] = "completed"
        steps[step_index]["review"] = review or "completed"


def request_fix(plan: dict[str, Any], issue: str) -> None:
    steps = plan.setdefault("steps", [])
    steps.append(
        {
            "id": f"fix_{len(steps) + 1}",
            "description": f"Fix review issue: {issue}",
            "status": "pending",
            "review": None,
        }
    )
    plan["status"] = "needs_revision"


def generate_revision_instructions(
    reviewing_agent: str,
    target_agent: str,
    failed_output: dict[str, Any],
    approval: dict[str, Any],
    context: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    with span(
        "generate_revision_instructions",
        "chain",
        {"reviewing_agent": reviewing_agent, "target_agent": target_agent, "run_id": run_id},
    ):
        return _generate_revision_instructions_impl(reviewing_agent, target_agent, failed_output, approval, context, run_id)


def _generate_revision_instructions_impl(
    reviewing_agent: str,
    target_agent: str,
    failed_output: dict[str, Any],
    approval: dict[str, Any],
    context: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    prompt = f"""You are {reviewing_agent}. You rejected or questioned {target_agent}'s work.
Generate concrete new instructions for {target_agent}: what is missing, how to improve it, what to retry, and what approval criteria must be met next.
Return JSON with: missing, improved_instructions, must_do_next, approval_criteria."""
    instructions = _llm_json(
        prompt,
        {"failed_output": failed_output, "approval": approval, "context": context, "shared_memory": read_memory(run_id, 80)},
        task_tier="cheap",
    )
    if not instructions:
        issues = approval.get("issues") or ["Reviewer requested another iteration."]
        instructions = {
            "missing": issues,
            "improved_instructions": f"Address these issues before resubmitting to {reviewing_agent}: " + "; ".join(str(i) for i in issues),
            "must_do_next": ["Review shared Redis memory", "Revise the plan", "Re-execute the weak steps", "Resubmit for approval"],
            "approval_criteria": ["All review issues are explicitly addressed", "Output is grounded in available evidence"],
        }
    append_memory(
        run_id,
        reviewing_agent,
        "revision_instructions",
        {"target_agent": target_agent, "instructions": instructions, "approval": approval},
    )
    return instructions


def review_agent_work(agent_name: str, objective: str, output: dict[str, Any], context: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    with span("review_agent_work", "chain", {"agent_name": agent_name, "run_id": run_id}):
        return _review_agent_work_impl(agent_name, objective, output, context, run_id)


def _review_agent_work_impl(agent_name: str, objective: str, output: dict[str, Any], context: dict[str, Any], run_id: str | None = None) -> dict[str, Any]:
    prompt = f"""You are the reviewer for {agent_name}.
Decide whether the agent should stop or continue. If it should continue, identify exactly what must be fixed.
Return JSON: approved (boolean), decision ("approve"|"revise"|"blocked"), issues (array), rationale."""
    reviewed = _llm_json(prompt, {"objective": objective, "output": output, "context": context, "shared_memory": read_memory(run_id, 40)}, task_tier="cheap")
    if not reviewed:
        issues = []
        if output.get("critical_error"):
            issues.append(str(output["critical_error"]))
        if output.get("requires_output") and not output.get("result"):
            issues.append("Required output missing.")
        reviewed = {
            "approved": not issues,
            "decision": "approve" if not issues else "revise",
            "issues": issues,
            "rationale": "Deterministic review based on required output and critical errors.",
        }
    append_memory(run_id, agent_name, "self_review", reviewed)
    return reviewed


def parent_approve(
    parent_agent: str,
    child_agent: str,
    child_plan: dict[str, Any],
    child_output: dict[str, Any],
    context: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    with span("parent_approve", "chain", {"parent_agent": parent_agent, "child_agent": child_agent, "run_id": run_id}):
        return _parent_approve_impl(parent_agent, child_agent, child_plan, child_output, context, run_id)


def _parent_approve_impl(
    parent_agent: str,
    child_agent: str,
    child_plan: dict[str, Any],
    child_output: dict[str, Any],
    context: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    prompt = f"""You are {parent_agent}. Review child agent {child_agent}.
The child may only stop if you approve. Check plan completion, evidence quality, warnings, and whether further research/reasoning is needed.
Return JSON: approved (boolean), decision ("approve"|"revise"|"blocked"), issues (array), feedback, reusable_context."""
    reviewed = _llm_json(
        prompt,
        {
            "child_plan": child_plan,
            "child_output": child_output,
            "context": context,
            "shared_memory": read_memory(run_id, 60),
        },
        task_tier="cheap",
    )
    if not reviewed:
        warnings = child_output.get("warnings") or []
        has_result = bool(
            child_output.get("result")
            or child_output.get("items")
            or child_output.get("markdown")
            or child_output.get("segmentation")
            or child_output.get("positioning")
            or child_output.get("channels")
            or child_output.get("subagents")
        )
        blocked = bool(warnings) and not has_result
        reviewed = {
            "approved": True if has_result or blocked else False,
            "decision": "blocked" if blocked else ("approve" if has_result else "revise"),
            "issues": [] if has_result or blocked else ["Child did not produce a usable result."],
            "feedback": "Approved with documented warnings." if warnings else "Approved.",
            "reusable_context": child_output.get("reusable_context") or {},
        }
    append_memory(
        run_id,
        parent_agent,
        "parent_approval",
        {"child_agent": child_agent, "approval": reviewed, "child_plan_status": child_plan.get("status")},
    )
    return reviewed


def run_planned_agent(
    agent_name: str,
    parent_agent: str,
    objective: str,
    context: dict[str, Any],
    fallback_steps: list[str],
    work_fn,
    run_id: str | None = None,
    max_iterations: int = 2,
    revision_fn=None,
) -> dict[str, Any]:
    with span(
        "run_planned_agent",
        "chain",
        {"agent_name": agent_name, "parent_agent": parent_agent, "run_id": run_id, "max_iterations": max_iterations},
    ):
        plan = create_agent_plan(agent_name, objective, context, fallback_steps, run_id, parent_agent)
        output: dict[str, Any] = {}
        approval: dict[str, Any] = {"approved": False, "decision": "not_reviewed", "issues": []}

        for iteration in range(max_iterations):
            with span(
                "run_planned_agent_iteration",
                "chain",
                {"agent_name": agent_name, "iteration": iteration + 1, "run_id": run_id},
            ):
                append_memory(run_id, agent_name, "iteration_started", {"iteration": iteration + 1, "plan": plan})
                output = work_fn(plan, context, iteration)
                for idx, step in enumerate(plan.get("steps") or []):
                    if step.get("status") == "pending":
                        complete_step(plan, idx, review="Executed during iteration.")

                self_review = review_agent_work(agent_name, objective, output, context, run_id)
                approval = parent_approve(parent_agent, agent_name, plan, output, {**context, "self_review": self_review}, run_id)
                if approval.get("approved"):
                    plan["status"] = "completed"
                    break
                issues = approval.get("issues") or self_review.get("issues") or ["Parent requested revision."]
                if revision_fn is not None:
                    revision = revision_fn(context, output, self_review, approval, iteration)
                    if revision:
                        append_memory(run_id, agent_name, "tool_call_revised", revision)
                request_fix(plan, "; ".join(str(issue) for issue in issues))
                append_memory(run_id, agent_name, "revision_requested", {"iteration": iteration + 1, "issues": issues})
        else:
            plan["status"] = "blocked"

        append_memory(run_id, agent_name, "work_finished", {"plan": plan, "output": output, "approval": approval})
        return {"plan": plan, "output": output, "approval": approval}


def _fallback_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Minimal non-LLM fallback: choose broad web research only.

    This keeps tests/local runs deterministic without pretending to be an
    autonomous strategist. Real autonomy requires an LLM provider
    (GTM_LLM_PROVIDER=vertex with GOOGLE_APPLICATION_CREDENTIALS, or
    GTM_LLM_PROVIDER=openai with OPENAI_API_KEY).
    """
    available = {tool["name"] for tool in tools}
    query = " ".join(
        str(v)
        for v in (
            user_input.get("product_name"),
            user_input.get("product_description"),
            user_input.get("target_customers"),
            "market competitors customer pain points pricing",
        )
        if v
    )
    calls: list[dict[str, Any]] = []
    if "web_research" in available:
        calls.append(
            {
                "tool_name": "web_research",
                "arguments": {"query": query[:500], "product_context": _product_context(user_input), "max_results": 8},
                "reason": "Fallback path: broad open-web evidence is most generally useful across product types.",
            }
        )
    return calls


def _broaden_query(query: str, user_input: dict[str, Any]) -> str:
    cleaned = re.sub(r'["()]', " ", query)
    cleaned = re.sub(r"\bsite:\S+", " ", cleaned)
    cleaned = re.sub(r"\b(OR|AND)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())
    fallback_bits = [
        user_input.get("product_name"),
        user_input.get("target_customers"),
        "GTM pain points competitors pricing customer acquisition",
    ]
    fallback = " ".join(str(bit) for bit in fallback_bits if bit)
    if len(cleaned.split()) < 4:
        return fallback[:500]
    return f"{cleaned} {fallback}"[:500]


def _split_competitor_calls(call: dict[str, Any], user_input: dict[str, Any]) -> list[dict[str, Any]]:
    args = dict(call.get("arguments") or {})
    raw_competitors = user_input.get("known_competitors") or []
    competitors = [str(c).strip() for c in raw_competitors if str(c).strip()]
    if len(competitors) < 2:
        query = str(args.get("query") or "")
        competitors = [part.strip(" .") for part in re.split(r"\s+(?:and|vs|versus)\s+|,", query) if "." in part or part.strip().istitle()]
    if len(competitors) < 2:
        return []
    product_context = str(args.get("product_context") or _product_context(user_input))
    max_results = _safe_int(args.get("max_results"), 5)
    return [
        {
            **call,
            "tool_name": "competitor_research",
            "arguments": {
                "query": f"{competitor} GTM strategy pricing positioning customer acquisition channels",
                "product_context": product_context,
                "max_results": max(3, min(max_results, 6)),
            },
            "reason": f"Adaptive retry: split combined competitor research into a focused search for {competitor}.",
        }
        for competitor in competitors[:6]
    ]


def revise_research_calls_for_retry(
    selected_calls: list[dict[str, Any]],
    user_input: dict[str, Any],
    output: dict[str, Any],
    self_review: dict[str, Any],
    approval: dict[str, Any],
) -> list[dict[str, Any]]:
    """Produce executable revised tool calls after a research retry rejection."""
    issues_text = " ".join(str(i) for i in (approval.get("issues") or []) + (self_review.get("issues") or [])).lower()
    result_items = output.get("items") or []
    result_warnings = output.get("warnings") or []
    zero_results = not result_items or "zero result" in issues_text or "no results" in issues_text
    needs_split = any(token in issues_text for token in ("combined", "separate", "split", "multiple", "missing", "no information"))
    if not zero_results and not result_warnings and not needs_split:
        return selected_calls

    revised: list[dict[str, Any]] = []
    for call in selected_calls:
        tool_name = str(call.get("tool_name") or "")
        args = dict(call.get("arguments") or {})
        query = str(args.get("query") or "")
        if tool_name == "competitor_research" and (
            "combined" in issues_text
            or "separate" in issues_text
            or "split" in issues_text
            or "multiple" in issues_text
            or "missing" in issues_text
            or "no information" in issues_text
            or len(user_input.get("known_competitors") or []) > 1
        ):
            split_calls = _split_competitor_calls(call, user_input)
            if split_calls:
                revised.extend(split_calls)
                continue

        if zero_results and tool_name == "crawl_search_results":
            revised.append(
                {
                    **call,
                    "tool_name": "web_research",
                    "arguments": {
                        "query": _broaden_query(query, user_input),
                        "product_context": args.get("product_context") or _product_context(user_input),
                        "max_results": max(5, _safe_int(args.get("max_results"), 5)),
                    },
                    "reason": "Adaptive retry: broad web search after crawl/search returned no usable evidence.",
                }
            )
            continue

        if zero_results and "query" in args:
            new_args = {
                **args,
                "query": _broaden_query(query, user_input),
                "max_results": max(5, _safe_int(args.get("max_results"), 5)),
            }
            revised.append({**call, "arguments": new_args, "reason": "Adaptive retry: broadened query after no usable evidence."})
            continue

        revised.append(call)

    return revised or selected_calls


def validate_research_calls(calls: list[dict[str, Any]], user_input: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    validated: list[dict[str, Any]] = []
    notes: list[dict[str, str]] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        tool_name = str(call.get("tool_name") or "")
        args = dict(call.get("arguments") or {})

        if tool_name == "competitor_research" and len(user_input.get("known_competitors") or []) > 1:
            split_calls = _split_competitor_calls(call, user_input)
            if split_calls:
                validated.extend(split_calls)
                notes.append({"tool_name": tool_name, "reason": "Split multi-competitor research into focused calls."})
                continue

        if tool_name == "crawl_search_results":
            query = str(args.get("query") or "")
            exact_phrases = query.count('"') // 2
            site_filters = len(re.findall(r"\bsite:\S+", query))
            boolean_ops = len(re.findall(r"\b(?:OR|AND)\b", query, flags=re.IGNORECASE))
            if exact_phrases >= 2 or site_filters >= 2 or (site_filters >= 1 and boolean_ops >= 1):
                validated.append(
                    {
                        **call,
                        "tool_name": "web_research",
                        "arguments": {
                            "query": _broaden_query(query, user_input),
                            "product_context": args.get("product_context") or _product_context(user_input),
                            "max_results": max(5, _safe_int(args.get("max_results"), 5)),
                        },
                        "reason": "Planner guardrail: broad web search before narrow forum crawl.",
                    }
                )
                notes.append({"tool_name": tool_name, "reason": "Rewrote narrow crawl_search_results query to web_research."})
                continue

            args["max_results"] = _clamp_int(args.get("max_results"), 3, 1, 3)
            args["max_pages_per_result"] = _clamp_int(args.get("max_pages_per_result"), 1, 1, 1)
            args["max_depth"] = _clamp_int(args.get("max_depth"), 1, 0, 1)

        if tool_name == "crawl_web":
            args["max_pages"] = _clamp_int(args.get("max_pages"), 8, 1, 8)
            args["max_depth"] = _clamp_int(args.get("max_depth"), 1, 0, 1)

        validated.append({**call, "arguments": args})
    return validated, notes


def plan_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    with span(
        "plan_research_calls",
        "chain",
        {"run_id": str(user_input.get("run_id") or ""), "tool_count": len(tools)},
    ):
        return _plan_research_calls_impl(user_input, tools)


def _plan_research_calls_impl(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = """You are the autonomous research supervisor for a GTM multi-agent system.
Choose only the research tools that are likely to produce useful evidence for this specific product.
Do not call every tool by default. For example:
- Internet/software/devtools products may justify web_research, competitor_research, and crawl_search_results (or crawl_web when you already have high-value URLs like docs/pricing pages).
- Physical products, food, local services, healthcare, or regulated categories may rely more on web_research/competitor_research and shallow crawl_search_results for public pages — avoid aggressive crawling when robots disallow it.
- Use crawl_web with explicit start_urls when you need rendered HTML depth (help centers, changelogs, forums, blogs). Use crawl_search_results when you need discovery + fetch in one step.
Create focused, source-specific queries. Return:
{
  "research_strategy": "short rationale",
  "calls": [
    {
      "tool_name": "...",
      "arguments": {
        "query": "...",
        "product_context": "...",
        "max_results": 5,
        "start_urls": ["https://..."],
        "max_pages": 10,
        "max_depth": 2,
        "same_domain_only": true,
        "respect_robots": true
      },
      "reason": "..."
    }
  ],
  "skipped_tools": [{"tool_name": "...", "reason": "..."}]
}
Include only arguments relevant to each tool (e.g. crawl_web requires start_urls; crawl_search_results requires query).
"""
    planned = _llm_json(
        prompt,
        {"user_input": user_input, "available_tools": tools, "shared_memory": read_memory(str(user_input.get("run_id") or ""), 50)},
        task_tier="standard",
    )
    if planned and isinstance(planned.get("calls"), list):
        calls, notes = validate_research_calls(planned.get("calls") or [], user_input)
        planned["calls"] = calls
        if notes:
            planned.setdefault("planner_guardrails", []).extend(notes)
        planned["autonomy_mode"] = "llm"
        return planned
    return {
        "autonomy_mode": "fallback",
        "research_strategy": "No LLM provider configured (GTM_LLM_PROVIDER + Vertex/OpenAI creds); using conservative broad web research fallback.",
        "calls": _fallback_research_calls(user_input, tools),
        "skipped_tools": [{"tool_name": "llm_planner", "reason": "Autonomous LLM planner not configured."}],
    }


def autonomous_research(
    user_input: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
    progress_callback=None,
    research_items_callback=None,
) -> dict[str, Any]:
    with span(
        "autonomous_research",
        "chain",
        {"run_id": run_id, "parent_agent": parent_agent, "has_revision_instructions": bool(additional_instructions)},
    ):
        return _autonomous_research_impl(user_input, run_id, parent_agent, additional_instructions, progress_callback, research_items_callback)


def _autonomous_research_impl(
    user_input: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
    progress_callback=None,
    research_items_callback=None,
) -> dict[str, Any]:
    started_at = time.monotonic()
    max_seconds = _env_int("GTM_RESEARCH_MAX_SECONDS", 240)
    max_tool_calls = _env_int("GTM_RESEARCH_MAX_TOOL_CALLS", 8)
    min_sources_for_approval = _env_int("GTM_RESEARCH_MIN_SOURCES_FOR_APPROVAL", 12)
    tool_call_count = 0
    if os.getenv("GTM_DISABLE_EXTERNAL_RESEARCH") == "true":
        disabled_plan = {
            "autonomy_mode": "disabled",
            "research_strategy": "External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true.",
            "calls": [],
            "skipped_tools": [],
        }
        disabled_parent_plan = create_agent_plan(
            "research_parent_agent",
            "Research is disabled; document the blocked state and request parent approval.",
            {"user_input": user_input},
            ["Confirm external research is disabled.", "Document missing evidence.", "Ask main agent for blocked-state approval."],
            run_id,
            parent_agent,
        )
        for idx in range(len(disabled_parent_plan.get("steps") or [])):
            complete_step(disabled_parent_plan, idx, "External research disabled; step documented.")
        approval = parent_approve(
            parent_agent,
            "research_parent_agent",
            disabled_parent_plan,
            {"warnings": ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."]},
            {"user_input": user_input},
            run_id,
        )
        return {
            "research_plan": disabled_plan,
            "items": [],
            "warnings": ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."],
            "tool_results": [],
            "research_bundle": merge_research([]),
            "research_parent_plan": disabled_parent_plan,
            "research_parent_approval": approval,
        }

    try:
        tools = list_research_tools()
    except Exception as e:
        error_plan = {
            "autonomy_mode": "error",
            "research_strategy": "Could not list research tools.",
            "calls": [],
        }
        error_parent_plan = create_agent_plan(
            "research_parent_agent",
            "Research tool registry is unavailable; document the blocked state.",
            {"user_input": user_input, "error": str(e)},
            ["Attempt to list research tools.", "Document the tool failure.", "Ask main agent for blocked-state approval."],
            run_id,
            parent_agent,
        )
        for idx in range(len(error_parent_plan.get("steps") or [])):
            complete_step(error_parent_plan, idx, "MCP server unavailable; step documented.")
        approval = parent_approve(
            parent_agent,
            "research_parent_agent",
            error_parent_plan,
            {"warnings": [f"Research tool registry unavailable: {e}"]},
            {"user_input": user_input},
            run_id,
        )
        return {
            "research_plan": error_plan,
            "items": [],
            "warnings": [f"Research tool registry unavailable: {e}"],
            "tool_results": [],
            "research_bundle": merge_research([]),
            "research_parent_plan": error_parent_plan,
            "research_parent_approval": approval,
        }

    research_parent_plan = create_agent_plan(
        "research_parent_agent",
        "Decide what market evidence is needed, choose relevant research tools, supervise subagents, and stop only after parent approval.",
        {
            "user_input": user_input,
            "available_tools": tools,
            "additional_instructions": additional_instructions or {},
            "shared_memory": read_memory(run_id, 50),
        },
        [
            "Inspect product details and available research tools.",
            "Choose relevant sources and formulate source-specific queries.",
            "Delegate selected calls to research subagents.",
            "Review subagent results and decide whether more research is required.",
            "Submit research bundle for main-agent approval.",
        ],
        run_id,
        parent_agent,
    )
    research_plan = plan_research_calls({**user_input, "run_id": run_id, "additional_instructions": additional_instructions or {}}, tools)
    if additional_instructions:
        research_plan["revision_instructions"] = additional_instructions
    complete_step(research_parent_plan, 0, "Available MCP tools inspected.")
    complete_step(research_parent_plan, 1, "Research calls selected.")

    tool_results: list[dict[str, Any]] = []
    calls = research_plan.get("calls") or []
    if not calls:
        research_plan.setdefault("skipped_tools", []).append(
            {"tool_name": "all", "reason": "Planner selected no research calls for this product/input."}
        )
    for call in calls:
        if tool_call_count >= max_tool_calls or (time.monotonic() - started_at) >= max_seconds:
            research_plan.setdefault("skipped_tools", []).append(
                {
                    "tool_name": str(call.get("tool_name") or "research_tool"),
                    "reason": "Skipped because the research budget was exhausted.",
                }
            )
            continue
        tool_name = str(call.get("tool_name") or "research_tool")
        subagent_name = f"{tool_name}_subagent"

        def _call_tool(_plan: dict[str, Any], _context: dict[str, Any], _iteration: int) -> dict[str, Any]:
            nonlocal tool_call_count
            selected_calls = list(_context.get("selected_calls") or [_context.get("selected_call")])
            selected_calls = [c for c in selected_calls if isinstance(c, dict)]
            remaining = max(0, max_tool_calls - tool_call_count)
            if remaining <= 0:
                return {
                    "result": {"items": [], "warnings": ["Research tool budget exhausted before this call."], "tool_name": "budget"},
                    "items": [],
                    "warnings": ["Research tool budget exhausted before this call."],
                    "reusable_context": {"result_count": 0, "budget_exhausted": True},
                }
            selected_calls = selected_calls[:remaining]
            tool_call_count += len(selected_calls)
            if callable(progress_callback):
                for selected_call in selected_calls:
                    try:
                        progress_callback(
                            str(selected_call.get("tool_name") or "research_tool"),
                            "research",
                            "Research tool call started",
                            {"iteration": _iteration + 1, "arguments": selected_call.get("arguments") or {}, "reason": selected_call.get("reason")},
                        )
                    except Exception:
                        pass
            results = call_research_tools(selected_calls)
            merged_items: list[ResearchItem] = []
            merged_warnings: list[str] = []
            for result in results:
                merged_items.extend(result.get("items") or [])
                merged_warnings.extend(result.get("warnings") or [])
                if callable(progress_callback):
                    try:
                        progress_callback(
                            str(result.get("tool_name") or "research_tool"),
                            "research",
                            "Research tool call finished",
                            {
                                "iteration": _iteration + 1,
                                "source_count": len(result.get("items") or []),
                                "warnings": result.get("warnings") or [],
                                "arguments": result.get("arguments") or {},
                            },
                        )
                    except Exception:
                        pass
                if callable(research_items_callback) and result.get("items"):
                    try:
                        research_items_callback(list(result.get("items") or []), result)
                    except Exception:
                        pass
            result = {
                "source_type": "other",
                "items": merged_items,
                "warnings": merged_warnings,
                "tool_name": "+".join(str(r.get("tool_name") or "research_tool") for r in results),
                "arguments": [r.get("arguments") or {} for r in results],
                "reason": "; ".join(str(r.get("reason") or "") for r in results if r.get("reason")),
                "tool_results": results,
            }
            return {
                "result": result,
                "items": result.get("items") or [],
                "warnings": result.get("warnings") or [],
                "reusable_context": {
                    "tool_name": result.get("tool_name"),
                    "query": result.get("arguments"),
                    "result_count": len(result.get("items") or []),
                    "approach": result.get("reason"),
                },
            }

        def _revise_tool_call(_context: dict[str, Any], output: dict[str, Any], self_review: dict[str, Any], approval: dict[str, Any], _iteration: int) -> dict[str, Any] | None:
            selected_calls = list(_context.get("selected_calls") or [_context.get("selected_call")])
            selected_calls = [c for c in selected_calls if isinstance(c, dict)]
            revised_calls = revise_research_calls_for_retry(selected_calls, user_input, output, self_review, approval)
            if revised_calls == selected_calls:
                return None
            _context["selected_calls"] = revised_calls
            _context["selected_call"] = revised_calls[0] if revised_calls else None
            return {"previous_calls": selected_calls, "revised_calls": revised_calls, "iteration": _iteration + 1}

        subagent = run_planned_agent(
            subagent_name,
            "research_parent_agent",
            f"Use research tool {tool_name} only if useful, collect evidence, and request parent approval before stopping.",
            {
                "selected_call": call,
                "selected_calls": [call],
                "user_input": user_input,
                "sibling_memory": read_memory(run_id, 75),
            },
            [
                "Read parent instructions and sibling memory.",
                "Execute the assigned research tool call.",
                "Normalize findings and warnings.",
                "Ask research parent for approval.",
            ],
            _call_tool,
            run_id,
            max_iterations=2,
            revision_fn=_revise_tool_call,
        )
        tool_results.append(
            {
                **(subagent["output"].get("result") or {}),
                "subagent_plan": subagent["plan"],
                "parent_approval": subagent["approval"],
            }
        )
    complete_step(research_parent_plan, 2, "Selected subagents executed.")

    items: list[ResearchItem] = []
    warnings: list[str] = []
    for result in tool_results:
        items.extend(result.get("items") or [])
        warnings.extend(result.get("warnings") or [])
    if not calls:
        warnings.append("Research planner selected no MCP calls.")
    research_output = {
        "research_plan": research_plan,
        "items": items,
        "warnings": warnings,
        "tool_results": tool_results,
        "research_bundle": merge_research(items),
        "budget": {
            "elapsed_seconds": round(time.monotonic() - started_at, 2),
            "tool_call_count": tool_call_count,
            "max_seconds": max_seconds,
            "max_tool_calls": max_tool_calls,
            "min_sources_for_approval": min_sources_for_approval,
        },
    }
    complete_step(research_parent_plan, 3, "Subagent results reviewed and merged.")
    fatal_warnings = [w for w in warnings if "registry unavailable" in str(w).lower()]
    if len(items) >= min_sources_for_approval and not fatal_warnings:
        parent_review = {
            "approved": True,
            "decision": "approved_with_warnings" if warnings else "approve",
            "issues": [],
            "feedback": "Deterministic research gate approved the layer because the source threshold was met.",
            "reusable_context": {"source_count": len(items), "warnings": warnings[:10], "budget": research_output["budget"]},
        }
        append_memory(run_id, parent_agent, "parent_approval", {"child_agent": "research_parent_agent", "approval": parent_review, "deterministic_gate": True})
    else:
        parent_review = parent_approve(parent_agent, "research_parent_agent", research_parent_plan, research_output, {"user_input": user_input}, run_id)
    if parent_review.get("approved"):
        complete_step(research_parent_plan, 4, "Main agent approved research layer.")
        research_parent_plan["status"] = "completed"
    else:
        request_fix(research_parent_plan, "; ".join(str(issue) for issue in parent_review.get("issues") or ["Main agent requested more research."]))
    research_output["research_parent_plan"] = research_parent_plan
    research_output["research_parent_approval"] = parent_review
    write_context_snapshot(run_id, {"research": research_output, "memory_tail": read_memory(run_id, 25)})
    return research_output


def synthesize_section(section_name: str, user_input: dict[str, Any], research: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    with span("synthesize_section", "chain", {"section_name": section_name, "evidence_count": len(research.get("items") or [])}):
        return _synthesize_section_impl(section_name, user_input, research, prior)


def _synthesize_section_impl(section_name: str, user_input: dict[str, Any], research: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    prompt = f"""You are a senior GTM agent responsible for the {section_name} layer.
You have full freedom to choose the structure and fields that are most useful for this product.
Do not force generic keys like value_props or messaging_angles unless they genuinely fit the evidence.
Ground every important claim in the provided evidence. If evidence is thin, say so explicitly.
Return a JSON object with your chosen structure."""
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "prior": prior or {}}, task_tier="standard")
    if llm:
        return llm

    # Non-LLM fallback stays evidence-derived and avoids fixed GTM strategy values.
    items = research.get("items") or []
    return {
        "mode": "fallback_without_llm",
        "section": section_name,
        "evidence_count": len(items),
        "evidence_summary": [item.get("summary") or item.get("title") for item in items[:5]],
        "next_step": f"Configure GTM_LLM_PROVIDER (vertex or openai) with credentials for autonomous {section_name} synthesis.",
    }


def run_reasoning_layer(
    user_input: dict[str, Any],
    research: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with span("run_reasoning_layer", "chain", {"run_id": run_id, "parent_agent": parent_agent}):
        return _run_reasoning_layer_impl(user_input, research, run_id, parent_agent, additional_instructions)


def _run_reasoning_layer_impl(
    user_input: dict[str, Any],
    research: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parent_plan = create_agent_plan(
        "reasoning_parent_agent",
        "Turn approved research into GTM reasoning. Decide which reasoning subagents are needed and approve their work before completion.",
        {
            "user_input": user_input,
            "research": research,
            "additional_instructions": additional_instructions or {},
            "shared_memory": read_memory(run_id, 75),
        },
        [
            "Review research approval and source quality.",
            "Delegate segmentation reasoning.",
            "Delegate positioning and messaging reasoning.",
            "Delegate channel strategy and experiment reasoning.",
            "Review all reasoning outputs and submit to main agent.",
        ],
        run_id,
        parent_agent,
    )
    complete_step(parent_plan, 0, "Approved research reviewed.")

    outputs: dict[str, Any] = {}
    specs = [
        ("segmentation_subagent", "segmentation", "Reason from evidence to customer segments, ICPs, personas, jobs, and unknowns."),
        ("positioning_subagent", "positioning_and_messaging", "Reason from evidence to category narrative, differentiation, objections, proof, and messaging."),
        ("channel_strategy_subagent", "channel_strategy_and_experiments", "Reason from evidence to launch channels, experiments, sequencing, and success metrics."),
    ]
    for idx, (agent_name, section_name, objective) in enumerate(specs, start=1):
        def _work(_plan: dict[str, Any], _context: dict[str, Any], _iteration: int, name: str = section_name) -> dict[str, Any]:
            result = synthesize_section(name, user_input, research, prior={**outputs, "shared_memory": read_memory(run_id, 75)})
            return {"result": result, "reusable_context": {"section": name, "keys": list(result.keys())}}

        subagent = run_planned_agent(
            agent_name,
            "reasoning_parent_agent",
            objective,
            {
                "user_input": user_input,
                "research": research,
                "prior_outputs": outputs,
                "additional_instructions": additional_instructions or {},
                "shared_memory": read_memory(run_id, 75),
            },
            [
                "Read research evidence and sibling memory.",
                "Create evidence-grounded reasoning output with a structure suited to this product.",
                "Review for unsupported claims and missing caveats.",
                "Ask reasoning parent for approval.",
            ],
            _work,
            run_id,
            max_iterations=2,
        )
        outputs[section_name] = subagent["output"].get("result") or {}
        outputs[f"{section_name}_plan"] = subagent["plan"]
        outputs[f"{section_name}_approval"] = subagent["approval"]
        complete_step(parent_plan, idx, f"{agent_name} approved by reasoning parent.")

    parent_output = {
        "segmentation": outputs.get("segmentation") or {},
        "positioning": outputs.get("positioning_and_messaging") or {},
        "channels": outputs.get("channel_strategy_and_experiments") or {},
        "subagents": outputs,
    }
    approval = parent_approve(parent_agent, "reasoning_parent_agent", parent_plan, parent_output, {"research": research}, run_id)
    if approval.get("approved"):
        complete_step(parent_plan, 4, "Main agent approved reasoning layer.")
        parent_plan["status"] = "completed"
    else:
        request_fix(parent_plan, "; ".join(str(issue) for issue in approval.get("issues") or ["Main agent requested reasoning revision."]))
    parent_output["reasoning_parent_plan"] = parent_plan
    parent_output["reasoning_parent_approval"] = approval
    parent_output["revision_instructions"] = additional_instructions or None
    write_context_snapshot(run_id, {"reasoning": parent_output, "memory_tail": read_memory(run_id, 25)})
    return parent_output


def synthesize_report_markdown(user_input: dict[str, Any], research: dict[str, Any], synthesis: dict[str, Any]) -> str | None:
    with span("synthesize_report_markdown", "chain", {"markdown_request": True}):
        return _synthesize_report_markdown_impl(user_input, research, synthesis)


def _synthesize_report_markdown_impl(user_input: dict[str, Any], research: dict[str, Any], synthesis: dict[str, Any]) -> str | None:
    prompt = """You are the final WriterAgent for an autonomous GTM system.
Write a professional GTM strategy document in Markdown. You may decide the section structure,
but it must include citations/source references where available, assumptions, and concrete next actions.
Do not use a generic template if the product calls for a different structure."""
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "synthesis": synthesis}, max_chars=24000, task_tier="premium")
    if not llm:
        return None
    markdown = llm.get("markdown") or llm.get("report") or llm.get("content")
    return str(markdown) if markdown else None


def run_writing_layer(
    user_input: dict[str, Any],
    research: dict[str, Any],
    reasoning: dict[str, Any],
    validation: dict[str, Any],
    fallback_writer,
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with span("run_writing_layer", "chain", {"run_id": run_id, "parent_agent": parent_agent}):
        return _run_writing_layer_impl(
            user_input, research, reasoning, validation, fallback_writer, run_id, parent_agent, additional_instructions
        )


def _run_writing_layer_impl(
    user_input: dict[str, Any],
    research: dict[str, Any],
    reasoning: dict[str, Any],
    validation: dict[str, Any],
    fallback_writer,
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parent_plan = create_agent_plan(
        "writing_parent_agent",
        "Create the final GTM strategy document from approved research and reasoning, review it, and request main-agent approval before completion.",
        {
            "user_input": user_input,
            "research": research,
            "reasoning": reasoning,
            "validation": validation,
            "additional_instructions": additional_instructions or {},
            "shared_memory": read_memory(run_id, 75),
        },
        [
            "Review approved research and reasoning context.",
            "Draft a product-specific GTM strategy document.",
            "Validate citations, assumptions, and actionability.",
            "Revise if review finds issues.",
            "Ask main agent for final approval.",
        ],
        run_id,
        parent_agent,
    )

    def _write(_plan: dict[str, Any], _context: dict[str, Any], _iteration: int) -> dict[str, Any]:
        markdown = synthesize_report_markdown(user_input, research, {**reasoning, "validation": validation}) or fallback_writer()
        critical_error = None
        if not markdown.strip():
            critical_error = "Writer produced an empty report."
        return {"markdown": markdown, "critical_error": critical_error, "reusable_context": {"markdown_chars": len(markdown)}}

    writer = run_planned_agent(
        "writer_agent",
        "writing_parent_agent",
        "Produce a final GTM report that is specific to this product and grounded in approved evidence.",
        {
            "user_input": user_input,
            "research": research,
            "reasoning": reasoning,
            "validation": validation,
            "additional_instructions": additional_instructions or {},
        },
        [
            "Read approved layer outputs.",
            "Draft GTM report.",
            "Check report for evidence, clarity, assumptions, and next actions.",
            "Ask writing parent for approval.",
        ],
        _write,
        run_id,
        max_iterations=2,
    )
    for idx in range(min(4, len(parent_plan.get("steps") or []))):
        complete_step(parent_plan, idx, "Writing layer step completed.")
    output = {"markdown": writer["output"].get("markdown") or "", "writer_plan": writer["plan"], "writer_approval": writer["approval"]}
    approval = parent_approve(parent_agent, "writing_parent_agent", parent_plan, output, {"validation": validation}, run_id)
    if approval.get("approved"):
        complete_step(parent_plan, 4, "Main agent approved final writing layer.")
        parent_plan["status"] = "completed"
    else:
        request_fix(parent_plan, "; ".join(str(issue) for issue in approval.get("issues") or ["Main agent requested writing revision."]))
    output["writing_parent_plan"] = parent_plan
    output["writing_parent_approval"] = approval
    output["revision_instructions"] = additional_instructions or None
    write_context_snapshot(run_id, {"writing": output, "memory_tail": read_memory(run_id, 25)})
    return output
