"""Workspace data completeness scoring."""

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


def compute_completeness(
    org: dict[str, Any],
    *,
    document_count: int = 0,
    competitor_count: int = 0,
) -> dict[str, Any]:
    profile = org.get("profile") or {}
    if not isinstance(profile, dict):
        profile = {}

    profile_checks = {
        field: bool(str(profile.get(field) or "").strip())
        for field in PROFILE_FIELDS
    }
    has_name = bool(str(org.get("name") or "").strip())
    has_website = bool(str(org.get("website_url") or "").strip())
    has_industry = bool(str(org.get("industry") or "").strip())
    has_brand_voice = profile_checks.get("brand_voice", False)
    has_documents = document_count > 0
    has_competitors = competitor_count > 0

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
    }

    total = len(checks)
    completed = sum(1 for v in checks.values() if v)
    percent = round((completed / total) * 100) if total else 0

    missing: list[str] = []
    if not has_documents:
        missing.append("documents")
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
        "ready_for_intelligence": has_documents,
        "ready_for_competitive": has_competitors,
        "ready_for_campaigns": has_documents and (has_brand_voice or bool(org.get("industry"))),
    }
