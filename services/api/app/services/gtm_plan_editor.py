from __future__ import annotations

from typing import Any


def edit_gtm_plan(
    *,
    company: dict[str, Any],
    plan: dict[str, Any],
    messages: list[dict[str, Any]],
    user_message: str,
) -> dict[str, Any]:
    """Return an updated plan and assistant reply for a company-scoped GTM chat turn."""
    from gtm_agents.llm import invoke_json

    system = (
        "You are a GTM plan editor. Update the provided GTM plan only for the selected company. "
        "Respect the company profile and recent messages. Return JSON with: "
        "assistant_reply (string), updated_markdown (string), updated_json (object), title (string optional)."
    )
    current_markdown = str(plan.get("content_markdown") or "")
    payload = {
        "company": {
            "name": company.get("name"),
            "description": company.get("description"),
            "industry": company.get("industry"),
            "target_customers": company.get("target_customers"),
            "geography": company.get("geography"),
            "business_model": company.get("business_model"),
            "stage": company.get("stage"),
            "goals": company.get("goals") or [],
            "known_competitors": company.get("known_competitors") or [],
            "constraints": company.get("constraints") or [],
        },
        "current_plan": {
            "title": plan.get("title") or "GTM plan",
            "markdown": current_markdown,
            "json": plan.get("content_json") or {},
        },
        "recent_messages": messages[-12:],
        "user_message": user_message,
    }
    result, _provider = invoke_json(system, payload, task_tier="standard")
    if isinstance(result, dict):
        updated_markdown = str(result.get("updated_markdown") or current_markdown).strip()
        assistant_reply = str(result.get("assistant_reply") or "I updated the GTM plan.").strip()
        current_json = plan.get("content_json") if isinstance(plan.get("content_json"), dict) else {}
        raw_json = result.get("updated_json")
        if isinstance(raw_json, dict) and raw_json:
            updated_json = raw_json
        else:
            updated_json = current_json
        title = str(result.get("title") or plan.get("title") or "GTM plan").strip()
        return {
            "assistant_reply": assistant_reply,
            "updated_markdown": updated_markdown or current_markdown,
            "updated_json": updated_json,
            "title": title,
        }

    fallback_note = f"\n\n## Requested change\n{user_message.strip()}\n"
    return {
        "assistant_reply": "I added your requested change to the plan notes so you can refine it from here.",
        "updated_markdown": (current_markdown.rstrip() + fallback_note).strip(),
        "updated_json": plan.get("content_json") or {},
        "title": str(plan.get("title") or "GTM plan"),
    }
