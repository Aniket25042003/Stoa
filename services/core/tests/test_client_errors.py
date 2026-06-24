"""Tests for client-safe error messages."""

from stoa_core.security.client_errors import client_safe_error_message


def test_sync_error_is_generic():
    assert client_safe_error_message("Connection refused to 10.0.0.1:5432", context="sync") == (
        "Sync failed. Contact support if the issue persists."
    )


def test_content_error_is_generic():
    msg = client_safe_error_message("Vertex API key invalid", context="content")
    assert msg and "failed" in msg
