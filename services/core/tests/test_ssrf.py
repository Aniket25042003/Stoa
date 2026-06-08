import pytest

from stoa_core.security.ssrf import assert_safe_fetch_url
from stoa_core.security.urls import is_safe_external_href, safe_storage_filename


def test_blocks_localhost():
    with pytest.raises(ValueError):
        assert_safe_fetch_url("https://localhost/admin")


def test_blocks_metadata_ip():
    with pytest.raises(ValueError):
        assert_safe_fetch_url("https://169.254.169.254/latest/meta-data/")


def test_allows_public_https():
    assert assert_safe_fetch_url("https://example.com/page") == "https://example.com/page"


def test_safe_storage_filename_strips_traversal():
    assert safe_storage_filename("../../secret.txt") == "secret.txt"


def test_is_safe_external_href_blocks_javascript():
    assert is_safe_external_href("javascript:alert(1)") is False
    assert is_safe_external_href("https://example.com") is True
