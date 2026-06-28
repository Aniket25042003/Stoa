"""
File: services/core/src/stoa_core/org/completeness.py
Layer: Application Source
Purpose: Implements completeness behavior for the application source.
Dependencies: standard library / local modules
"""


from __future__ import annotations

from typing import Any

PROFILE_FIELDS = (
    "target_customers",
    "business_model",
    "stage",
    "goals",
    "brand_voice",
    "known_competitors_notes",
)


def _profile_field_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return bool(str(value).strip())


def compute_completeness(
    org: dict[str, Any],
    *,
    document_count: int = 0,
    competitor_count: int = 0,
    integration_count: int = 0,
    canonical_deal_count: int = 0,
) -> dict[str, Any]:
    """Handles compute completeness logic for the surrounding Stoa workflow.

    Args:
        org (dict[str, Any]): Input value used by this workflow step.
        document_count (int): Input value used by this workflow step.
        competitor_count (int): Input value used by this workflow step.
        integration_count (int): Input value used by this workflow step.
        canonical_deal_count (int): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    profile = org.get("profile") or {}
    if not isinstance(profile, dict):
        profile = {}

    profile_checks = {
        field: _profile_field_filled(profile.get(field))
        for field in PROFILE_FIELDS
    }
    has_name = bool(str(org.get("name") or "").strip())
    has_website = bool(str(org.get("website_url") or "").strip())
    has_industry = bool(str(org.get("industry") or "").strip())
    has_brand_voice = profile_checks.get("brand_voice", False)
    has_documents = document_count > 0
    has_competitors = competitor_count > 0
    has_integration = integration_count > 0
    has_structured_data = canonical_deal_count > 0 or integration_count > 0

    checks = {
        "has_name": has_name,
        "has_website": has_website,
        "has_industry": has_industry,
        "has_target_customers": profile_checks.get("target_customers", False),
        "has_business_model": profile_checks.get("business_model", False),
        "has_stage": profile_checks.get("stage", False),
        "has_goals": profile_checks.get("goals", False),
        "has_brand_voice": has_brand_voice,
        "has_documents": has_documents,
        "has_competitors": has_competitors,
        "has_integration": has_integration,
        "has_structured_data": has_structured_data,
    }

    total = len(checks)
    completed = sum(1 for v in checks.values() if v)
    percent = round((completed / total) * 100) if total else 0

    missing: list[str] = []
    if not has_documents and not has_structured_data:
        missing.append("documents_or_integration")
    if not has_competitors:
        missing.append("competitors")
    if not has_brand_voice:
        missing.append("brand_voice")
    if not profile_checks.get("target_customers"):
        missing.append("target_customers")
    if not has_website:
        missing.append("website_url")
    if not has_industry:
        missing.append("industry")

    return {
        "percent": percent,
        "completed": completed,
        "total": total,
        "checks": checks,
        "missing": missing,
        "ready_for_intelligence": has_documents or has_structured_data,
        "ready_for_competitive": has_competitors,
        "ready_for_campaigns": has_documents and (has_brand_voice or bool(org.get("industry"))),
    }
