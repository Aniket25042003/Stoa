"""
File: services/core/tests/test_integrations.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test integrations in the test suite.
Dependencies: stoa_core
"""


from __future__ import annotations

from stoa_core.integrations.crypto import decrypt_credentials, encrypt_credentials
from stoa_core.integrations.csv_structured import parse_csv_content
from stoa_core.integrations.registry import get_connector, list_providers


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


def test_get_hubspot_connector():
    connector = get_connector("hubspot")
    assert connector.provider == "hubspot"
    info = connector.provider_info()
    assert info.auth_type == "oauth"
