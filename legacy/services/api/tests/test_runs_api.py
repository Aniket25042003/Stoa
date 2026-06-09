from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps.auth import verify_supabase_jwt
from app.main import app
from app.routers import runs as runs_router


def test_create_run_enqueues_master_plan_without_blocking(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def _insert_run(user_id, payload, master_plan=None, status="awaiting_plan_approval", company_id=None):
        calls["insert"] = {
            "user_id": user_id,
            "payload": payload,
            "master_plan": master_plan,
            "status": status,
            "company_id": company_id,
        }
        return "00000000-0000-0000-0000-000000000123"

    class _Task:
        @staticmethod
        def delay(run_id, user_id, *args):
            calls["delay"] = {"run_id": run_id, "user_id": user_id, "args": args}

    monkeypatch.setattr(runs_router.supabase_db, "insert_run", _insert_run)
    monkeypatch.setattr(runs_router, "create_master_plan_task", _Task)
    app.dependency_overrides[verify_supabase_jwt] = lambda: "user-123"
    try:
        client = TestClient(app)
        res = client.post("/v1/runs", json={"product_description": "A test product for GTM research."})
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json()["status"] == "planning"
    assert calls["insert"]["status"] == "planning"  # type: ignore[index]
    assert calls["insert"]["master_plan"] == {}  # type: ignore[index]
    assert calls["delay"] == {
        "run_id": "00000000-0000-0000-0000-000000000123",
        "user_id": "user-123",
        "args": (),
    }
