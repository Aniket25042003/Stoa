"""
File: services/api/tests/conftest.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for conftest in the test suite.
Dependencies: Supabase, stoa_core
"""


from __future__ import annotations

import os

os.environ.setdefault("STOA_ENV", "development")
import uuid

import jwt
import pytest
from supabase import Client, create_client

from stoa_core.org.roles import seed_system_roles_for_org


def _integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS", "").strip().lower() in {"1", "true", "yes"}


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"{name} not set")
    return value


@pytest.fixture(scope="session")
def supabase_admin() -> Client:
    if not _integration_enabled():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 to run live Supabase RLS tests")
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


@pytest.fixture(scope="session")
def supabase_anon() -> Client:
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


@pytest.fixture(scope="session")
def jwt_secret() -> str:
    return _require_env("SUPABASE_JWT_SECRET")


def sign_test_jwt(user_id: str, secret: str, supabase_url: str) -> str:
    issuer = f"{supabase_url.rstrip('/')}/auth/v1"
    return jwt.encode(
        {"sub": user_id, "aud": "authenticated", "role": "authenticated", "iss": issuer},
        secret,
        algorithm="HS256",
    )


@pytest.fixture()
def rls_test_context(supabase_admin: Client, jwt_secret: str):
    """Create two isolated orgs with viewer memberships and yield anon clients."""
    suffix = uuid.uuid4().hex[:8]
    email_a = f"rls-viewer-a-{suffix}@example.com"
    email_b = f"rls-viewer-b-{suffix}@example.com"
    password = f"Test-{suffix}!Aa1"

    user_a = supabase_admin.auth.admin.create_user(
        {"email": email_a, "password": password, "email_confirm": True}
    ).user
    user_b = supabase_admin.auth.admin.create_user(
        {"email": email_b, "password": password, "email_confirm": True}
    ).user
    assert user_a and user_b

    org_a = supabase_admin.table("organizations").insert({"name": f"RLS A {suffix}", "slug": f"rls-a-{suffix}"}).execute().data[0]
    org_b = supabase_admin.table("organizations").insert({"name": f"RLS B {suffix}", "slug": f"rls-b-{suffix}"}).execute().data[0]

    roles_a = seed_system_roles_for_org(supabase_admin, org_a["id"])
    roles_b = seed_system_roles_for_org(supabase_admin, org_b["id"])

    supabase_admin.table("memberships").insert(
        {"org_id": org_a["id"], "user_id": user_a.id, "role": "viewer", "role_id": roles_a["viewer"]}
    ).execute()
    supabase_admin.table("memberships").insert(
        {"org_id": org_b["id"], "user_id": user_b.id, "role": "viewer", "role_id": roles_b["viewer"]}
    ).execute()

    url = os.environ["SUPABASE_URL"]
    anon_key = os.environ["SUPABASE_ANON_KEY"]

    client_a = create_client(url, anon_key)
    client_a.postgrest.auth(sign_test_jwt(user_a.id, jwt_secret, url))
    client_b = create_client(url, anon_key)
    client_b.postgrest.auth(sign_test_jwt(user_b.id, jwt_secret, url))

    ctx = {
        "admin": supabase_admin,
        "client_a": client_a,
        "client_b": client_b,
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "roles_a": roles_a,
        "roles_b": roles_b,
    }
    yield ctx

    try:
        supabase_admin.table("memberships").delete().eq("user_id", user_a.id).execute()
        supabase_admin.table("memberships").delete().eq("user_id", user_b.id).execute()
        supabase_admin.table("org_roles").delete().eq("org_id", org_a["id"]).execute()
        supabase_admin.table("org_roles").delete().eq("org_id", org_b["id"]).execute()
        supabase_admin.table("organizations").delete().eq("id", org_a["id"]).execute()
        supabase_admin.table("organizations").delete().eq("id", org_b["id"]).execute()
        supabase_admin.auth.admin.delete_user(user_a.id)
        supabase_admin.auth.admin.delete_user(user_b.id)
    except Exception:
        pass
