"""Auth/session workflow helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.org.roles import role_key_from_membership
from stoa_core.security.permissions import SYSTEM_ROLE_OWNER


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def provider_from_claims(claims: dict[str, Any]) -> str:
    app_meta = claims.get("app_metadata") or {}
    provider = app_meta.get("provider")
    if provider:
        return str(provider)
    providers = app_meta.get("providers")
    if isinstance(providers, list) and providers:
        return str(providers[0])
    return "email"


def email_from_claims(claims: dict[str, Any]) -> str:
    return str(claims.get("email") or "").strip().lower()


def user_is_email_verified(user_id: str, claims: dict[str, Any]) -> bool:
    provider = provider_from_claims(claims)
    if provider != "email":
        return True
    if claims.get("email_confirmed_at") or claims.get("confirmed_at"):
        return True

    sb = get_supabase_admin()
    try:
        response = sb.auth.admin.get_user_by_id(user_id)
        user = getattr(response, "user", None) or response
        confirmed = getattr(user, "email_confirmed_at", None) or getattr(user, "confirmed_at", None)
        return bool(confirmed)
    except Exception:
        return False


def get_or_create_user_profile(user_id: str, claims: dict[str, Any]) -> dict[str, Any]:
    sb = get_supabase_admin()
    email = email_from_claims(claims)
    provider = provider_from_claims(claims)
    user_meta = claims.get("user_metadata") or {}
    full_name = user_meta.get("full_name") or user_meta.get("name")
    verified = user_is_email_verified(user_id, claims)
    verified_at = utc_now_iso() if verified else None

    existing = sb.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
    row = (existing.data or [None])[0]
    payload = {
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "auth_provider": provider,
    }
    if verified_at and not (row or {}).get("email_verified_at"):
        payload["email_verified_at"] = verified_at

    if row:
        sb.table("user_profiles").update({k: v for k, v in payload.items() if v is not None}).eq("user_id", user_id).execute()
        row.update({k: v for k, v in payload.items() if v is not None})
        return row

    if verified_at:
        payload["email_verified_at"] = verified_at
    res = sb.table("user_profiles").insert(payload).execute()
    return (res.data or [payload])[0]


def list_memberships(user_id: str) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select(
            "id, org_id, role, role_id, created_at, "
            "org_roles(id, name, role_key, permissions, is_system), "
            "organizations(id, name, slug, website_url, industry, profile, onboarding_completed_at)"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def get_membership_optional(user_id: str, org_id: str | None = None) -> dict[str, Any] | None:
    memberships = list_memberships(user_id)
    if not memberships:
        return None
    if org_id:
        for m in memberships:
            if m.get("org_id") == org_id:
                return m
        return None
    sb = get_supabase_admin()
    profile = sb.table("user_profiles").select("last_active_org_id").eq("user_id", user_id).limit(1).execute()
    active = (profile.data or [None])[0]
    active_org = (active or {}).get("last_active_org_id")
    if active_org:
        for m in memberships:
            if m.get("org_id") == active_org:
                return m
    return memberships[0]


def onboarding_needed(profile: dict[str, Any], membership: dict[str, Any] | None) -> bool:
    return onboarding_needed_for_user(profile.get("user_id", ""), profile=profile, membership=membership)


def onboarding_needed_for_user(
    user_id: str,
    claims: dict[str, Any] | None = None,
    *,
    profile: dict[str, Any] | None = None,
    membership: dict[str, Any] | None = None,
) -> bool:
    sb = get_supabase_admin()
    if profile is None:
        if claims:
            profile = get_or_create_user_profile(user_id, claims)
        else:
            res = sb.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
            profile = (res.data or [None])[0] or {}

    memberships = list_memberships(user_id)
    if not memberships:
        return True
    if not profile.get("onboarding_completed_at"):
        return True

    if membership is None:
        membership = get_membership_optional(user_id)

    if membership:
        org = membership.get("organizations") or {}
        role_key = role_key_from_membership(membership)
        if role_key == SYSTEM_ROLE_OWNER and not org.get("onboarding_completed_at"):
            return True
    else:
        # User has memberships but no resolvable active org — not blocked from app shell
        return False

    return False


def suggest_company_from_email(email: str) -> dict[str, str | None]:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    generic = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "proton.me", "protonmail.com"}
    if not domain or domain in generic:
        return {"name": None, "website_url": None}
    company = domain.split(".")[0].replace("-", " ").title()
    return {"name": company, "website_url": f"https://{domain}"}


def is_legacy_auto_provisioned_org(
    org: dict[str, Any],
    *,
    full_name: str | None,
    email: str,
) -> bool:
    """True for orgs created by the removed handle_new_user_org signup trigger."""
    if org.get("onboarding_completed_at"):
        return False
    name = (org.get("name") or "").strip()
    if not name:
        return True
    if full_name and name.casefold() == str(full_name).strip().casefold():
        return True
    local_part = email.split("@")[0] if "@" in email else "workspace"
    if name == f"{local_part}'s workspace":
        return True
    return False


def filter_memberships_for_display(
    memberships: list[dict[str, Any]],
    *,
    full_name: str | None,
    email: str,
) -> list[dict[str, Any]]:
    """Hide legacy signup stubs when the user has at least one onboarded org."""
    has_completed_org = any((m.get("organizations") or {}).get("onboarding_completed_at") for m in memberships)
    if not has_completed_org:
        return memberships
    return [
        m
        for m in memberships
        if not is_legacy_auto_provisioned_org(
            m.get("organizations") or {},
            full_name=full_name,
            email=email,
        )
    ]


def delete_legacy_stub_orgs_for_user(
    user_id: str,
    *,
    keep_org_id: str,
    full_name: str | None,
    email: str,
) -> None:
    """Remove abandoned signup stub orgs after the user completes real onboarding."""
    sb = get_supabase_admin()
    for membership in list_memberships(user_id):
        org_id = membership.get("org_id")
        if not org_id or org_id == keep_org_id:
            continue
        org = membership.get("organizations") or {}
        if not is_legacy_auto_provisioned_org(org, full_name=full_name, email=email):
            continue
        if role_key_from_membership(membership) != SYSTEM_ROLE_OWNER:
            continue
        member_count = (
            sb.table("memberships").select("id", count="exact").eq("org_id", org_id).execute().count or 0
        )
        if member_count > 1:
            continue
        sb.table("organizations").delete().eq("id", org_id).execute()
