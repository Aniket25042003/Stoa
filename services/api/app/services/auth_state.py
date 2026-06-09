"""Auth/session workflow helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


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


def get_membership_optional(user_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select(
            "id, org_id, role, created_at, "
            "organizations(id, name, slug, website_url, industry, profile, onboarding_completed_at)"
        )
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def onboarding_needed(profile: dict[str, Any], membership: dict[str, Any] | None) -> bool:
    if not membership:
        return True
    org = membership.get("organizations") or {}
    return not bool(profile.get("onboarding_completed_at") and org.get("onboarding_completed_at"))
