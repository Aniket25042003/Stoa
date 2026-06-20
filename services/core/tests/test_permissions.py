"""
File: services/core/tests/test_permissions.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test permissions in the test suite.
Dependencies: stoa_core
"""

from stoa_core.security.permissions import (
    builtin_role_permissions,
    catalog_for_ui,
    grantable_permissions,
    permission_set_satisfies,
)


def test_builtin_owner_has_all_permissions():
    perms = set(builtin_role_permissions("owner"))
    assert "org:delete" in perms
    assert "roles:manage" in perms


def test_builtin_viewer_is_read_only():
    perms = set(builtin_role_permissions("viewer"))
    assert "documents:read" in perms
    assert "documents:write" not in perms


def test_permission_boundary_subset():
    actor = set(builtin_role_permissions("analyst"))
    requested = {"documents:read", "documents:write"}
    assert permission_set_satisfies(actor, requested)
    assert not permission_set_satisfies(actor, {"roles:manage"})


def test_catalog_excludes_owner_reserved():
    grantable = set(grantable_permissions())
    assert "org:delete" not in grantable
    assert len(catalog_for_ui()) >= 5
