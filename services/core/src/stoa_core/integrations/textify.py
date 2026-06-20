"""
File: services/core/src/stoa_core/integrations/textify.py
Layer: Core Integration Connectors
Purpose: Implements textify behavior for the core integration connectors.
Dependencies: standard library / local modules
"""


from __future__ import annotations

from typing import Any


def account_to_text(row: dict[str, Any]) -> str:
    """Handles account to text logic for the surrounding Stoa workflow.

    Args:
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    lines = [f"# Account: {row.get('name') or 'Unknown'}"]
    if row.get("domain"):
        lines.append(f"Domain: {row['domain']}")
    if row.get("industry"):
        lines.append(f"Industry: {row['industry']}")
    if row.get("employee_count_range"):
        lines.append(f"Company size: {row['employee_count_range']}")
    if row.get("lifecycle_stage"):
        lines.append(f"Lifecycle stage: {row['lifecycle_stage']}")
    if row.get("country"):
        lines.append(f"Country: {row['country']}")
    return "\n".join(lines)


def contact_to_text(row: dict[str, Any]) -> str:
    """Handles contact to text logic for the surrounding Stoa workflow.

    Args:
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    lines = [f"# Contact: {row.get('name') or row.get('email') or 'Unknown'}"]
    if row.get("email"):
        lines.append(f"Email: {row['email']}")
    if row.get("title"):
        lines.append(f"Title: {row['title']}")
    if row.get("department"):
        lines.append(f"Department: {row['department']}")
    tags = row.get("persona_tags") or []
    if tags:
        lines.append(f"Personas: {', '.join(tags)}")
    return "\n".join(lines)


def deal_to_text(row: dict[str, Any]) -> str:
    """Handles deal to text logic for the surrounding Stoa workflow.

    Args:
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    lines = [f"# Deal: {row.get('name') or 'Unknown'}"]
    if row.get("amount") is not None:
        currency = row.get("currency") or "USD"
        lines.append(f"Amount: {currency} {row['amount']}")
    if row.get("stage"):
        lines.append(f"Stage: {row['stage']}")
    if row.get("pipeline"):
        lines.append(f"Pipeline: {row['pipeline']}")
    if row.get("is_won") is not None:
        lines.append(f"Won: {row['is_won']}")
    if row.get("is_closed") is not None:
        lines.append(f"Closed: {row['is_closed']}")
    if row.get("loss_reason"):
        lines.append(f"Loss reason: {row['loss_reason']}")
    if row.get("owner_name"):
        lines.append(f"Owner: {row['owner_name']}")
    return "\n".join(lines)


def interaction_to_text(row: dict[str, Any]) -> str:
    """Handles interaction to text logic for the surrounding Stoa workflow.

    Args:
        row (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    itype = row.get("interaction_type") or "interaction"
    title = row.get("title") or itype.replace("_", " ").title()
    lines = [f"# {title}", f"Type: {itype}"]
    if row.get("occurred_at"):
        lines.append(f"Date: {row['occurred_at']}")
    participants = row.get("participants") or []
    if participants:
        lines.append(f"Participants: {participants}")
    lines.append("")
    lines.append(row.get("body_text") or "")
    return "\n".join(lines)
