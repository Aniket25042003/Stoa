from __future__ import annotations

import json
import os
from typing import Any

from gtm_agents.memory import append_memory, read_memory, write_context_snapshot
from gtm_agents.mcp_client import call_research_tools, list_research_tools
from gtm_agents.observability import span
from gtm_agents.state import ResearchItem
from gtm_agents.tools.research import merge_research


def _llm_json(system: str, payload: dict[str, Any], max_chars: int = 16000) -> dict[str, Any] | None:
    model = os.getenv("GTM_AGENT_MODEL") or os.getenv("GTM_SYNTHESIS_MODEL")
    if not model or not os.getenv("OPENAI_API_KEY"):
        return None
    payload_keys = list(payload.keys()) if isinstance(payload, dict) else []
    with span(
        "llm_json",
        "llm",
        {
            "model": model,
            "system_preview": (system[:400] + "…") if len(system) > 400 else system,
            "payload_keys": payload_keys,
            "max_chars": max_chars,
        },
    ):
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model=model, temperature=0.25)
            msg = llm.invoke(
                [
                    ("system", system + "\nReturn only valid JSON. Do not wrap it in markdown."),
                    ("human", json.dumps(payload, default=str)[:max_chars]),
                ]
            )
            content = str(getattr(msg, "content", "")).strip()
            if content.startswith("```"):
                content = content.strip("`")
                content = content.removeprefix("json").strip()
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


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
    planned = _llm_json(prompt, {"objective": objective, "context": context, "shared_memory": read_memory(run_id, 30)})
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
    reviewed = _llm_json(prompt, {"objective": objective, "output": output, "context": context, "shared_memory": read_memory(run_id, 40)})
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
                request_fix(plan, "; ".join(str(issue) for issue in issues))
                append_memory(run_id, agent_name, "revision_requested", {"iteration": iteration + 1, "issues": issues})
        else:
            plan["status"] = "blocked"

        append_memory(run_id, agent_name, "work_finished", {"plan": plan, "output": output, "approval": approval})
        return {"plan": plan, "output": output, "approval": approval}


def _fallback_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Minimal non-LLM fallback: choose broad web research only.

    This keeps tests/local runs deterministic without pretending to be an
    autonomous strategist. Real autonomy requires GTM_AGENT_MODEL.
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


def plan_research_calls(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    with span(
        "plan_research_calls",
        "chain",
        {"run_id": str(user_input.get("run_id") or ""), "tool_count": len(tools)},
    ):
        return _plan_research_calls_impl(user_input, tools)


def _plan_research_calls_impl(user_input: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = """You are the autonomous research supervisor for a GTM multi-agent system.
Choose only the MCP tools that are likely to produce useful evidence for this specific product.
Do not call every tool by default. For example:
- Internet/software/devtools products may justify Reddit, X, web, and competitor search.
- Physical products, food, local services, healthcare, or regulated categories may rely more on web/competitor research.
- Use social/forum tools only when the target buyers likely discuss this category there.
Create focused, source-specific queries. Return:
{
  "research_strategy": "short rationale",
  "calls": [
    {"tool_name": "...", "arguments": {"query": "...", "product_context": "...", "max_results": 5}, "reason": "..."}
  ],
  "skipped_tools": [{"tool_name": "...", "reason": "..."}]
}
"""
    planned = _llm_json(prompt, {"user_input": user_input, "available_tools": tools, "shared_memory": read_memory(str(user_input.get("run_id") or ""), 50)})
    if planned and isinstance(planned.get("calls"), list):
        planned["autonomy_mode"] = "llm"
        return planned
    return {
        "autonomy_mode": "fallback",
        "research_strategy": "No GTM_AGENT_MODEL/OPENAI_API_KEY configured; using conservative broad web research fallback.",
        "calls": _fallback_research_calls(user_input, tools),
        "skipped_tools": [{"tool_name": "llm_planner", "reason": "Autonomous LLM planner not configured."}],
    }


def autonomous_research(
    user_input: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with span(
        "autonomous_research",
        "chain",
        {"run_id": run_id, "parent_agent": parent_agent, "has_revision_instructions": bool(additional_instructions)},
    ):
        return _autonomous_research_impl(user_input, run_id, parent_agent, additional_instructions)


def _autonomous_research_impl(
    user_input: dict[str, Any],
    run_id: str | None = None,
    parent_agent: str = "main_agent",
    additional_instructions: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
            "research_strategy": "Could not list MCP research tools.",
            "calls": [],
        }
        error_parent_plan = create_agent_plan(
            "research_parent_agent",
            "Research MCP server is unavailable; document the blocked state.",
            {"user_input": user_input, "error": str(e)},
            ["Attempt to list MCP tools.", "Document MCP failure.", "Ask main agent for blocked-state approval."],
            run_id,
            parent_agent,
        )
        for idx in range(len(error_parent_plan.get("steps") or [])):
            complete_step(error_parent_plan, idx, "MCP server unavailable; step documented.")
        approval = parent_approve(
            parent_agent,
            "research_parent_agent",
            error_parent_plan,
            {"warnings": [f"MCP research server unavailable: {e}"]},
            {"user_input": user_input},
            run_id,
        )
        return {
            "research_plan": error_plan,
            "items": [],
            "warnings": [f"MCP research server unavailable: {e}"],
            "tool_results": [],
            "research_bundle": merge_research([]),
            "research_parent_plan": error_parent_plan,
            "research_parent_approval": approval,
        }

    research_parent_plan = create_agent_plan(
        "research_parent_agent",
        "Decide what market evidence is needed, choose relevant MCP research tools, supervise subagents, and stop only after parent approval.",
        {
            "user_input": user_input,
            "available_tools": tools,
            "additional_instructions": additional_instructions or {},
            "shared_memory": read_memory(run_id, 50),
        },
        [
            "Inspect product details and available MCP tools.",
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
        tool_name = str(call.get("tool_name") or "research_tool")
        subagent_name = f"{tool_name}_subagent"

        def _call_tool(_plan: dict[str, Any], _context: dict[str, Any], _iteration: int, selected_call: dict[str, Any] = call) -> dict[str, Any]:
            result = call_research_tools([selected_call])[0]
            return {
                "result": result,
                "items": result.get("items") or [],
                "warnings": result.get("warnings") or [],
                "reusable_context": {
                    "tool_name": selected_call.get("tool_name"),
                    "query": (selected_call.get("arguments") or {}).get("query"),
                    "result_count": len(result.get("items") or []),
                    "approach": selected_call.get("reason"),
                },
            }

        subagent = run_planned_agent(
            subagent_name,
            "research_parent_agent",
            f"Use MCP tool {tool_name} only if useful, collect evidence, and request parent approval before stopping.",
            {
                "selected_call": call,
                "user_input": user_input,
                "sibling_memory": read_memory(run_id, 75),
            },
            [
                "Read parent instructions and sibling memory.",
                "Execute the assigned MCP tool call.",
                "Normalize findings and warnings.",
                "Ask research parent for approval.",
            ],
            _call_tool,
            run_id,
            max_iterations=2,
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
    }
    complete_step(research_parent_plan, 3, "Subagent results reviewed and merged.")
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
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "prior": prior or {}})
    if llm:
        return llm

    # Non-LLM fallback stays evidence-derived and avoids fixed GTM strategy values.
    items = research.get("items") or []
    return {
        "mode": "fallback_without_llm",
        "section": section_name,
        "evidence_count": len(items),
        "evidence_summary": [item.get("summary") or item.get("title") for item in items[:5]],
        "next_step": f"Configure GTM_AGENT_MODEL and OPENAI_API_KEY for autonomous {section_name} synthesis.",
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
    llm = _llm_json(prompt, {"user_input": user_input, "research": research, "synthesis": synthesis}, max_chars=24000)
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
