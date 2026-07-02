"""
File: services/api/app/routers/onboarding.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Pydantic, stoa_core
"""


from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt, verify_supabase_jwt_payload, verify_supabase_jwt_payload_verified
from app.deps.rate_limit import check_rate_limit
from app.routers.orgs import OrgProfileUpdate
from app.tasks.enrichment import enrich_company, seed_competitors_from_onboarding
from app.services.document_ingestion import queue_text_document
from app.services.audit import write_audit
from app.services.auth_state import (
    delete_legacy_stub_orgs_for_user,
    email_from_claims,
    filter_memberships_for_display,
    get_or_create_user_profile,
    list_memberships,
    onboarding_needed_for_user,
    suggest_company_from_email,
    user_is_email_verified,
    utc_now_iso,
)
from app.services.org_summary import build_completeness_for_org
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.ingestion.embed import EmbeddingUnavailableError
from stoa_core.org.roles import seed_system_roles_for_org
from stoa_core.rag.ingest import ingest_knowledge, profile_to_knowledge_text
from stoa_core.enrichment.jobs import pending_jobs_for_org
from stoa_core.security.permissions import SYSTEM_ROLE_OWNER, SYSTEM_ROLE_VIEWER
from stoa_core.security.ssrf import assert_safe_fetch_url

router = APIRouter(prefix="/v1/onboarding", tags=["onboarding"])

logger = logging.getLogger(__name__)
MAX_OWNER_ORGS_PER_USER = 10


class ProfileHints(BaseModel):
    """Manage ProfileHints behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    role_type: str | None = None
    job_title: str | None = None
    department: str | None = None
    notes: str | None = None


class TeammateInvite(BaseModel):
    """Manage TeammateInvite behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role_id: str | None = None
    profile_hints: ProfileHints | None = None


class OnboardingCompleteBody(BaseModel):
    """Manage OnboardingCompleteBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    mode: str = Field(pattern="^(owner_setup|invitee_profile)$")
    org_id: str | None = None
    name: str | None = Field(default=None, max_length=200)
    website_url: str | None = None
    industry: str | None = None
    role_type: str | None = None
    job_title: str | None = None
    use_case: str | None = None
    profile: OrgProfileUpdate | None = None
    seed_title: str | None = None
    seed_content: str | None = None
    teammate_invites: list[TeammateInvite] = Field(default_factory=list)


def _required_steps(mode: str, prefilled: dict[str, Any]) -> list[str]:
    """Handles  required steps logic for the surrounding Stoa workflow.

    Args:
        mode (str): Input value used by this workflow step.
        prefilled (dict[str, Any]): Input value used by this workflow step.

    Returns:
        list[str]: Result produced for the caller.
    """
    if mode == "invitee_profile":
        steps = []
        if not prefilled.get("role_type"):
            steps.append("role")
        if not prefilled.get("job_title"):
            steps.append("profile")
        if not steps:
            steps.append("profile")
        return steps
    steps = ["role", "company", "market"]
    steps.append("seed")
    steps.append("team")
    return steps


def _validate_website_url(url: str | None) -> str | None:
    if url is None or not str(url).strip():
        return None
    try:
        return assert_safe_fetch_url(str(url).strip())
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


def _resolve_invitee_membership(user_id: str, org_id: str | None, profile: dict[str, Any]) -> dict[str, Any]:
    memberships = list_memberships(user_id)
    if not memberships:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No organization membership found")
    if org_id:
        try:
            resolved = str(uuid.UUID(org_id))
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid org_id") from exc
        match = next((m for m in memberships if m["org_id"] == resolved), None)
        if not match:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization access denied")
        return match
    hinted = (profile.get("metadata") or {}).get("invite_org_id")
    if hinted:
        match = next((m for m in memberships if m["org_id"] == hinted), None)
        if match:
            return match
    return memberships[0]


def _resolve_mode(user_id: str, profile: dict[str, Any], memberships: list[dict[str, Any]]) -> str:
    """Handles  resolve mode logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.
        profile (dict[str, Any]): Input value used by this workflow step.
        memberships (list[dict[str, Any]]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    if not memberships:
        return "owner_setup"
    if not profile.get("onboarding_completed_at"):
        # Check if user is invitee to completed org
        for m in memberships:
            org = m.get("organizations") or {}
            role_row = m.get("org_roles") or {}
            if org.get("onboarding_completed_at") and role_row.get("role_key") != SYSTEM_ROLE_OWNER:
                return "invitee_profile"
        return "owner_setup"
    for m in memberships:
        org = m.get("organizations") or {}
        role_row = m.get("org_roles") or {}
        if role_row.get("role_key") == SYSTEM_ROLE_OWNER and not org.get("onboarding_completed_at"):
            return "owner_setup"
    return "complete"


@router.get("/context")
def get_onboarding_context(claims: dict[str, Any] = Depends(verify_supabase_jwt_payload)) -> dict[str, Any]:
    """Handles get onboarding context logic for the surrounding Stoa workflow.

    Args:
        claims (dict[str, Any]): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    user_id = str(claims["sub"])
    profile = get_or_create_user_profile(user_id, claims)
    memberships = list_memberships(user_id)
    email = email_from_claims(claims)
    mode = _resolve_mode(user_id, profile, memberships)
    email_verified = user_is_email_verified(user_id, claims)
    hints = (profile.get("metadata") or {}).get("invite_profile_hints") or {}
    prefilled = {
        **suggest_company_from_email(email),
        "role_type": profile.get("role_type") or hints.get("role_type"),
        "job_title": profile.get("job_title") or hints.get("job_title"),
        "full_name": profile.get("full_name"),
        "email": email,
    }
    if not email_verified:
        return {
            "mode": mode,
            "needs_onboarding": onboarding_needed_for_user(user_id, claims, profile=profile),
            "needs_email_verification": True,
            "required_steps": _required_steps(mode, prefilled),
            "prefilled": {"email": email},
            "memberships": [],
        }
    return {
        "mode": mode,
        "needs_onboarding": onboarding_needed_for_user(user_id, claims, profile=profile),
        "memberships": [
            {
                "org_id": m["org_id"],
                "role_name": (m.get("org_roles") or {}).get("name") or m.get("role"),
                "org_name": (m.get("organizations") or {}).get("name"),
                "onboarding_completed_at": (m.get("organizations") or {}).get("onboarding_completed_at"),
            }
            for m in filter_memberships_for_display(
                memberships,
                full_name=profile.get("full_name"),
                email=email,
            )
        ],
        "prefilled": prefilled,
        "required_steps": _required_steps(mode, prefilled),
    }


@router.get("/status")
def onboarding_status(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    """Handles onboarding status logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    profile_res = (
        sb.table("user_profiles")
        .select("last_active_org_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    profile_row = (profile_res.data or [None])[0] or {}
    target_org = profile_row.get("last_active_org_id")
    if not target_org:
        memberships = list_memberships(user_id)
        if memberships:
            target_org = memberships[0]["org_id"]
    if not target_org:
        return {"ready": False, "reason": "no_org"}

    kb_res = (
        sb.table("knowledge_items")
        .select("id, status")
        .eq("org_id", target_org)
        .eq("kind", "company_profile")
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    item = (kb_res.data or [None])[0]

    pending_jobs = (
        sb.table("ingestion_jobs")
        .select("id", count="exact")
        .eq("org_id", target_org)
        .in_("status", ["queued", "running"])
        .execute()
    )
    jobs_pending = (pending_jobs.count or 0) > 0
    enrichment_pending = pending_jobs_for_org(target_org) > 0

    partial_ready = bool(item) and not jobs_pending
    return {
        "ready": partial_ready and not enrichment_pending,
        "partial_ready": partial_ready,
        "org_id": target_org,
        "knowledge_item_id": item.get("id") if item else None,
        "pending_ingestion_jobs": pending_jobs.count or 0,
        "pending_enrichment_jobs": pending_jobs_for_org(target_org),
    }


@router.post("/complete")
def complete_onboarding(
    body: OnboardingCompleteBody,
    claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified),
) -> dict[str, Any]:
    """Handles complete onboarding logic for the surrounding Stoa workflow.

    Args:
        body (OnboardingCompleteBody): Input value used by this workflow step.
        claims (dict[str, Any]): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    user_id = str(claims["sub"])
    email = email_from_claims(claims)
    sb = get_supabase_admin()
    completed_at = utc_now_iso()
    profile_payload = body.profile.model_dump(exclude_none=True) if body.profile else {}
    profile = get_or_create_user_profile(user_id, claims)

    user_updates = {
        k: v
        for k, v in {
            "role_type": body.role_type,
            "job_title": body.job_title,
            "use_case": body.use_case,
            "onboarding_completed_at": completed_at,
        }.items()
        if v is not None
    }
    if user_updates:
        sb.table("user_profiles").update(user_updates).eq("user_id", user_id).execute()

    org: dict[str, Any] | None = None
    org_id: str | None = None
    seed_job_id: str | None = None

    if body.mode == "owner_setup":
        check_rate_limit(user_id, limit_per_minute=3, scope="org_create")
        owner_memberships = [
            m
            for m in list_memberships(user_id)
            if (m.get("org_roles") or {}).get("role_key") == SYSTEM_ROLE_OWNER or m.get("role") == SYSTEM_ROLE_OWNER
        ]
        if len(owner_memberships) >= MAX_OWNER_ORGS_PER_USER:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"You can create at most {MAX_OWNER_ORGS_PER_USER} organizations",
            )
        if not body.name or not body.name.strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Company name is required")
        website_url = _validate_website_url(body.website_url)
        slug_base = body.name.lower().replace(" ", "-")[:70]
        slug = f"{slug_base}-{uuid.uuid4().hex[:8]}"
        org_res = (
            sb.table("organizations")
            .insert(
                {
                    "name": body.name.strip(),
                    "slug": slug,
                    "website_url": website_url,
                    "industry": body.industry,
                    "profile": profile_payload,
                    "onboarding_completed_at": completed_at,
                }
            )
            .execute()
        )
        org = (org_res.data or [None])[0]
        if not org:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create organization")
        org_id = org["id"]
        role_map = seed_system_roles_for_org(sb, org_id, created_by=user_id)
        owner_role_id = role_map[SYSTEM_ROLE_OWNER]
        sb.table("memberships").insert(
            {
                "org_id": org_id,
                "user_id": user_id,
                "role": SYSTEM_ROLE_OWNER,
                "role_id": owner_role_id,
            }
        ).execute()
        sb.table("user_profiles").update({"last_active_org_id": org_id}).eq("user_id", user_id).execute()
        write_audit(org_id, user_id, "org.created", "organization", org_id, {"name": body.name})
        write_audit(org_id, user_id, "onboarding.completed", "organization", org_id)
        delete_legacy_stub_orgs_for_user(
            user_id,
            keep_org_id=org_id,
            full_name=profile.get("full_name"),
            email=email,
        )

        user_profile_context = {
            "role_type": body.role_type,
            "job_title": body.job_title,
            "use_case": body.use_case,
        }
        try:
            ingest_knowledge(
                org_id,
                kind="company_profile",
                title=f"{org.get('name', 'Company')} profile",
                text=profile_to_knowledge_text(org, user_profile=user_profile_context),
                feature_origin="onboarding",
                uri=f"org:{org_id}:company_profile",
                metadata={"source": "onboarding", **{k: v for k, v in user_profile_context.items() if v}},
            )
        except EmbeddingUnavailableError as exc:
            logger.warning(
                "Onboarding company profile KB ingest skipped (embeddings unavailable): %s",
                exc,
            )
        enrich_company.delay(org_id, user_id=user_id, idempotency_suffix="onboarding")

        competitor_notes = profile_payload.get("known_competitors_notes")
        if isinstance(competitor_notes, str) and competitor_notes.strip():
            seed_competitors_from_onboarding.delay(org_id, competitor_notes.strip(), user_id=user_id)

        if body.seed_content and body.seed_content.strip():
            try:
                _doc, job = queue_text_document(
                    org_id=org_id,
                    user_id=user_id,
                    title=body.seed_title or "Onboarding notes",
                    content=body.seed_content.strip(),
                    doc_type="note",
                    feature_origin="onboarding",
                )
                seed_job_id = job["id"] if job else None
            except ValueError:
                pass

        viewer_role_id = role_map.get(SYSTEM_ROLE_VIEWER)
        for invite in body.teammate_invites:
            email = invite.email.strip().lower()
            if not email:
                continue
            from app.services.invites import hash_invite_token, invite_expires_at, new_invite_token

            token = new_invite_token()
            role_id = invite.role_id or viewer_role_id
            sb.table("org_invites").insert(
                {
                    "org_id": org_id,
                    "email": email,
                    "role": "viewer",
                    "role_id": role_id,
                    "token_hash": hash_invite_token(token),
                    "invited_by": user_id,
                    "expires_at": invite_expires_at(),
                    "profile_hints": (invite.profile_hints.model_dump(exclude_none=True) if invite.profile_hints else {}),
                }
            ).execute()

    elif body.mode == "invitee_profile":
        active = _resolve_invitee_membership(user_id, body.org_id, profile)
        org_id = active["org_id"]
        org = active.get("organizations") or {}
        sb.table("user_profiles").update({"last_active_org_id": org_id}).eq("user_id", user_id).execute()
        write_audit(org_id, user_id, "onboarding.profile_completed", "user_profile", user_id)

    completeness = build_completeness_for_org(org) if org else {}
    return {
        "status": "completed",
        "org": org,
        "org_id": org_id,
        "completeness": completeness,
        "seed_job_id": seed_job_id if body.mode == "owner_setup" else None,
    }
