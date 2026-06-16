"""Tests for legacy auto-provisioned org filtering."""

from __future__ import annotations

from app.services.auth_state import (
    filter_memberships_for_display,
    is_legacy_auto_provisioned_org,
)


def _membership(org_id: str, name: str, *, onboarding_completed_at: str | None = None) -> dict:
    return {
        "org_id": org_id,
        "organizations": {
            "id": org_id,
            "name": name,
            "onboarding_completed_at": onboarding_completed_at,
        },
    }


def test_legacy_org_named_after_user_full_name_is_stub() -> None:
    org = {"name": "Aniket Patel", "onboarding_completed_at": None}
    assert is_legacy_auto_provisioned_org(org, full_name="Aniket Patel", email="aniket@gmail.com")


def test_completed_org_is_not_stub_even_with_personal_name() -> None:
    org = {"name": "Aniket Patel", "onboarding_completed_at": "2026-01-01T00:00:00Z"}
    assert not is_legacy_auto_provisioned_org(org, full_name="Aniket Patel", email="aniket@gmail.com")


def test_filter_hides_stub_when_completed_org_exists() -> None:
    memberships = [
        _membership("stub", "Aniket Patel"),
        _membership("real", "Stoa Labs", onboarding_completed_at="2026-01-01T00:00:00Z"),
    ]
    filtered = filter_memberships_for_display(
        memberships,
        full_name="Aniket Patel",
        email="aniket@gmail.com",
    )
    assert [m["org_id"] for m in filtered] == ["real"]


def test_filter_keeps_stub_when_no_completed_org() -> None:
    memberships = [_membership("stub", "Aniket Patel")]
    filtered = filter_memberships_for_display(
        memberships,
        full_name="Aniket Patel",
        email="aniket@gmail.com",
    )
    assert len(filtered) == 1
