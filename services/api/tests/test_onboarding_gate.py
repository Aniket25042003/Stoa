"""Tests for onboarding gating on org access."""

from app.services.auth_state import onboarding_needed_for_user


def test_owner_can_access_seeded_org_without_completed_timestamp():
    profile = {
        "user_id": "user-1",
        "onboarding_completed_at": "2026-06-26T20:21:03+00:00",
    }
    membership = {
        "org_roles": {"role_key": "owner"},
        "organizations": {
            "name": "Stoa",
            "website_url": "https://stoa-analytics.demo",
            "industry": "B2B SaaS - Marketing Analytics",
            "profile": {
                "target_customers": "VP Marketing",
                "business_model": "PLG",
            },
        },
    }
    assert onboarding_needed_for_user("user-1", profile=profile, membership=membership) is False


def test_owner_blocked_when_org_profile_incomplete():
    profile = {
        "user_id": "user-1",
        "onboarding_completed_at": "2026-06-26T20:21:03+00:00",
    }
    membership = {
        "org_roles": {"role_key": "owner"},
        "organizations": {
            "name": "Stoa Analytics",
            "profile": {},
        },
    }
    assert onboarding_needed_for_user("user-1", profile=profile, membership=membership) is True
