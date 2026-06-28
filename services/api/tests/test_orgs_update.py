"""Regression tests for org update helpers."""

from app.routers.orgs import _update_idempotency_suffix


def test_update_idempotency_suffix_handles_nested_profile():
    updates = {
        "profile": {
            "goals": ["expand ICP", "improve win rate"],
            "brand_voice": "confident",
        },
        "industry": "B2B SaaS",
    }
    suffix = _update_idempotency_suffix(updates)
    assert len(suffix) == 8
    assert suffix == _update_idempotency_suffix(updates)
