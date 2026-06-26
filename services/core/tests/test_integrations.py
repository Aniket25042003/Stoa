"""
File: services/core/tests/test_integrations.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for integrations in the test suite.
"""

from __future__ import annotations

from stoa_core.integrations.crypto import decrypt_credentials, encrypt_credentials
from stoa_core.integrations.csv_structured import parse_csv_content
from stoa_core.integrations.google_oauth import google_oauth_configured
from stoa_core.integrations.oauth_refresh import maybe_refresh_credentials, refresh_salesforce_token
from stoa_core.integrations.provider_capabilities import connectable_for, list_providers_for_api, oauth_available_for
from stoa_core.integrations.registry import get_connector, list_providers

MARKETING_PROVIDER_IDS = {
    "hubspot",
    "salesforce",
    "gong",
    "intercom",
    "zendesk",
    "reviews",
    "reddit",
    "posthog",
    "ga4",
    "notion",
    "google_drive",
    "slack",
    "jira",
}


def test_encrypt_decrypt_roundtrip(monkeypatch):
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    monkeypatch.setenv("INTEGRATION_CREDENTIALS_KEY", key)
    from stoa_core.config import get_settings

    get_settings.cache_clear()

    original = {"access_token": "secret-token", "refresh_token": "refresh"}
    blob = encrypt_credentials(original)
    restored = decrypt_credentials(blob)
    assert restored == original


def test_detect_csv_columns():
    content = "email,company,deal_amount,stage\na@co.com,Acme,1000,Won\n"
    headers, mapping = parse_csv_content(content)
    assert "email" in headers
    assert mapping.get("email") == "email"
    assert mapping.get("company") == "company"
    assert mapping.get("deal_amount") == "deal_amount"
    assert mapping.get("deal_stage") == "stage"


def test_detect_csv_columns_ignores_loose_role_matches():
    content = "Role Based Access,Email Address,Account Name\nuser@acme.com,Acme Corp,Admin\n"
    headers, mapping = parse_csv_content(content)
    assert mapping.get("email") == "Email Address"
    assert mapping.get("company") == "Account Name"
    assert mapping.get("title") is None


def test_registry_lists_providers():
    providers = list_providers()
    ids = {p.id for p in providers}
    assert "hubspot" in ids
    assert "csv_structured" in ids
    assert "gong" in ids


def test_marketing_catalog_parity():
    providers = list_providers()
    ids = {p.id for p in providers}
    assert MARKETING_PROVIDER_IDS.issubset(ids)
    assert "csv_structured" in ids


def test_get_hubspot_connector():
    connector = get_connector("hubspot")
    assert connector.provider == "hubspot"
    info = connector.provider_info()
    assert info.auth_type == "oauth"


def test_platform_managed_connectable_without_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    from stoa_core.config import get_settings

    get_settings.cache_clear()
    reddit = get_connector("reddit")
    assert connectable_for(reddit) is False


def test_platform_managed_connectable_with_token(monkeypatch):
    monkeypatch.setenv("APIFY_API_TOKEN", "test-token")
    from stoa_core.config import get_settings

    get_settings.cache_clear()
    reddit = get_connector("reddit")
    assert connectable_for(reddit) is True


def test_slack_supports_credential_without_oauth_env(monkeypatch):
    monkeypatch.delenv("SLACK_CLIENT_ID", raising=False)
    monkeypatch.delenv("SLACK_CLIENT_SECRET", raising=False)
    from stoa_core.config import get_settings

    get_settings.cache_clear()
    slack = get_connector("slack")
    info = slack.provider_info()
    assert info.supports_credential_auth is True
    assert connectable_for(slack) is True
    assert oauth_available_for(slack) is False


def test_google_oauth_not_configured_by_default(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    from stoa_core.config import get_settings

    get_settings.cache_clear()
    assert google_oauth_configured() is False
    ga4 = get_connector("ga4")
    assert oauth_available_for(ga4) is False


def test_providers_for_api_shape():
    providers = list_providers_for_api()
    assert providers
    sample = next(p for p in providers if p["id"] == "hubspot")
    assert "oauth_available" in sample
    assert "connectable" in sample
    assert "missing_env" in sample


def test_salesforce_refresh_preserves_instance_url(monkeypatch):
    def fake_post(url, data=None, **kwargs):
        class Resp:
            status_code = 200

            def json(self):
                return {
                    "access_token": "new-access",
                    "instance_url": "https://example.my.salesforce.com",
                }

        return Resp()

    import httpx

    monkeypatch.setattr(httpx.Client, "post", lambda self, url, **kw: fake_post(url, **kw))
    monkeypatch.setenv("SALESFORCE_CLIENT_ID", "id")
    monkeypatch.setenv("SALESFORCE_CLIENT_SECRET", "secret")
    from stoa_core.config import get_settings

    get_settings.cache_clear()

    creds = {"access_token": "old", "refresh_token": "rt"}
    refreshed = refresh_salesforce_token(creds, {"environment": "production"})
    assert refreshed["access_token"] == "new-access"
    assert refreshed["instance_url"] == "https://example.my.salesforce.com"


def test_maybe_refresh_skips_api_token_auth():
    creds = {"api_token": "z", "email": "a@b.com"}
    assert maybe_refresh_credentials("zendesk", creds) == creds


def test_scope_merge_requires_slack_channels():
    from stoa_core.integrations.scope import merge_scope_patch, validate_scope

    errors = validate_scope("slack", {})
    assert "Select at least one Slack channel" in errors[0]

    merged = merge_scope_patch(
        "slack",
        {},
        {"channel_ids": ["C1"], "scope_configured": True, "scope_labels": {"C1": "general"}},
    )
    assert merged["channel_ids"] == ["C1"]
    assert merged["scope_configured"] is True


def test_scope_merge_rejects_empty_ga4():
    from stoa_core.integrations.scope import merge_scope_patch

    try:
        merge_scope_patch("ga4", {}, {"scope_configured": True})
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "GA4" in str(exc)


def test_removed_uri_prefixes_slack_channel():
    from stoa_core.integrations.scope import removed_uri_prefixes

    old = {"channel_ids": ["C1", "C2"]}
    new = {"channel_ids": ["C2"]}
    prefixes = removed_uri_prefixes("slack", old, new)
    assert prefixes == ["slack:channel:C1"]


def test_zendesk_all_tickets_scope_merge():
    from stoa_core.integrations.scope import merge_scope_patch

    merged = merge_scope_patch(
        "zendesk",
        {},
        {"view_ids": ["__all__"], "scope_configured": True},
    )
    assert merged["sync_all_tickets"] is True
    assert merged["view_ids"] == []


def test_providers_expose_resource_selection_mode():
    providers = list_providers_for_api()
    slack = next(p for p in providers if p["id"] == "slack")
    assert slack.get("resource_selection_mode") == "required"
    assert "channel" in (slack.get("resource_kinds") or [])
