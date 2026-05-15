from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps.auth import verify_supabase_jwt
from app.main import app
from app.routers import companies as companies_router


def test_create_company_accepts_onboarding_profile(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def _insert_company(user_id, name, description=None, brand_voice=None, **profile):
        calls["insert"] = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "brand_voice": brand_voice,
            "profile": profile,
        }
        return "company-1"

    monkeypatch.setattr(companies_router.supabase_db, "insert_company", _insert_company)
    app.dependency_overrides[verify_supabase_jwt] = lambda: "user-123"
    try:
        client = TestClient(app)
        res = client.post(
            "/v1/companies",
            json={
                "name": "Acme",
                "description": "AI CRM",
                "industry": "SaaS",
                "target_customers": "Seed-stage founders",
                "goals": ["Launch"],
                "onboarding_completed": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json() == {"id": "company-1"}
    assert calls["insert"]["profile"]["industry"] == "SaaS"  # type: ignore[index]
    assert "onboarding_completed_at" in calls["insert"]["profile"]  # type: ignore[index]


def test_gtm_plan_upload_requires_company_ownership(monkeypatch) -> None:
    monkeypatch.setattr(companies_router.supabase_db, "get_company", lambda _cid: {"id": "company-1", "user_id": "other"})
    app.dependency_overrides[verify_supabase_jwt] = lambda: "user-123"
    try:
        client = TestClient(app)
        res = client.post(
            "/v1/companies/company-1/gtm-plan/upload",
            json={"title": "Plan", "content_markdown": "# Plan\n\nA detailed GTM plan for Acme."},
        )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 404


def test_gtm_plan_message_updates_active_plan(monkeypatch) -> None:
    calls: dict[str, object] = {}

    monkeypatch.setattr(companies_router.supabase_db, "get_company", lambda _cid: {"id": "company-1", "user_id": "user-123", "name": "Acme"})
    monkeypatch.setattr(
        companies_router.supabase_db,
        "get_active_gtm_plan",
        lambda _cid: {"id": "plan-1", "title": "Plan", "content_markdown": "# Plan", "content_json": {}},
    )
    monkeypatch.setattr(companies_router.supabase_db, "list_gtm_plan_messages", lambda _cid: [])
    monkeypatch.setattr(companies_router.supabase_db, "insert_gtm_plan_message", lambda *args, **kwargs: "msg-1")

    def _update_plan(plan_id, **kwargs):
        calls["update"] = {"plan_id": plan_id, **kwargs}
        return {"id": plan_id, **kwargs}

    monkeypatch.setattr(companies_router.supabase_db, "update_company_gtm_plan", _update_plan)
    monkeypatch.setattr(
        companies_router,
        "edit_gtm_plan",
        lambda **_kwargs: {
            "assistant_reply": "Updated.",
            "updated_markdown": "# Updated plan",
            "updated_json": {"changed": True},
            "title": "Updated plan",
        },
    )
    app.dependency_overrides[verify_supabase_jwt] = lambda: "user-123"
    try:
        client = TestClient(app)
        res = client.post("/v1/companies/company-1/gtm-plan/messages", json={"content": "Tighten ICP"})
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json()["assistant"]["content"] == "Updated."
    assert calls["update"]["content_markdown"] == "# Updated plan"  # type: ignore[index]
