"""Tests for Jira JQL scope validation."""

from __future__ import annotations

import pytest

from stoa_core.integrations.scope import assert_safe_jira_jql


def test_jira_jql_requires_project_filter_without_keys() -> None:
    with pytest.raises(ValueError, match="project filter"):
        assert_safe_jira_jql("ORDER BY updated DESC")


def test_jira_jql_must_reference_selected_projects() -> None:
    with pytest.raises(ValueError, match="selected Jira projects"):
        assert_safe_jira_jql('project = "OTHER" ORDER BY updated DESC', project_keys=["ENG"])


def test_jira_jql_accepts_project_scoped_query() -> None:
    jql = assert_safe_jira_jql('project in ("ENG") ORDER BY updated DESC', project_keys=["ENG"])
    assert "ENG" in jql
