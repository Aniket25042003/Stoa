"""
File: services/api/app/services/audit.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: Supabase, stoa_core
"""


from __future__ import annotations

from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.pii import redact_json


def write_audit(
    org_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Handles write audit logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.
        action (str): Input value used by this workflow step.
        resource_type (str): Input value used by this workflow step.
        resource_id (str | None): Input value used by this workflow step.
        metadata (dict[str, Any] | None): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    sb.table("audit_log").insert(
        {
            "org_id": org_id,
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": redact_json(metadata or {}),
        }
    ).execute()
