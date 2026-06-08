"""Audit log writes."""

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
