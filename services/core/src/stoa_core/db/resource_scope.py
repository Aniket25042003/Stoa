"""
File: services/core/src/stoa_core/db/resource_scope.py
Layer: Core Database
Purpose: Verify that a resource row belongs to the expected organization.
Dependencies: Supabase, stoa_core
"""

from __future__ import annotations

import uuid

from stoa_core.db.supabase import get_supabase_admin


def _parse_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value}") from exc


def verify_org_resource(
    table: str,
    resource_id: str,
    org_id: str,
    *,
    select: str = "id, org_id",
    id_column: str = "id",
) -> dict:
    """Load a row and assert it belongs to org_id."""
    resource_id = _parse_uuid(resource_id, f"{table}_id")
    org_id = _parse_uuid(org_id, "org_id")
    sb = get_supabase_admin()
    res = (
        sb.table(table)
        .select(select)
        .eq(id_column, resource_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise ValueError(f"{table} resource not found for organization: {resource_id}")
    return row
