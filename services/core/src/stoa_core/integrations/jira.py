"""
File: services/core/src/stoa_core/integrations/jira.py
Layer: Core Integration Connectors
Purpose: Implements jira behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_jira_projects
from stoa_core.integrations.scope import assert_safe_jira_jql
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "jira"


@register_connector
class JiraConnector(BaseConnector):
    """Manage JiraConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "jira"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="jira",
            name="Jira",
            auth_type="api_key",
            description="Import Jira issues and comments as customer feedback signals.",
            resource_selection_mode="required",
            resource_kinds=["project"],
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles connect with credentials logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        domain = credentials.get("domain", "").strip().rstrip("/")
        email = credentials.get("email", "").strip()
        api_token = credentials.get("api_token", "").strip()
        if not domain or not email or not api_token:
            raise ValueError("Jira domain, email, and api_token are required")
        return {
            "domain": domain,
            "email": email,
            "api_token": api_token,
            "provider_metadata": {"domain": domain},
        }

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return list_jira_projects(credentials, metadata)

    @classmethod
    def sync(
        cls,
        org_id: str,
        connection: dict[str, Any],
        *,
        credentials: dict[str, Any],
        cursor: dict[str, Any],
        full_backfill: bool = False,
    ) -> SyncResult:
        """Handles sync logic for the surrounding Stoa workflow.

        Args:
            org_id (str): Input value used by this workflow step.
            connection (dict[str, Any]): Input value used by this workflow step.
            credentials (dict[str, Any]): Input value used by this workflow step.
            cursor (dict[str, Any]): Input value used by this workflow step.
            full_backfill (bool): Input value used by this workflow step.

        Returns:
            SyncResult: Result produced for the caller.
        """
        result = SyncResult()
        metadata = connection.get("provider_metadata") or {}
        domain = metadata.get("domain") or credentials.get("domain")
        project_keys = metadata.get("project_keys") or []
        jql = metadata.get("jql")
        if not jql and project_keys:
            quoted = ", ".join(f'"{k}"' for k in project_keys)
            jql = f"project in ({quoted}) ORDER BY updated DESC"
        if not jql:
            result.error = "No Jira projects selected — configure access first"
            return result
        try:
            jql = assert_safe_jira_jql(str(jql), project_keys=project_keys)
        except ValueError as exc:
            result.error = str(exc)
            return result
        auth = httpx.BasicAuth(credentials["email"], credentials["api_token"])
        start_at = int(cursor.get("start_at", 0))

        try:
            with httpx.Client(timeout=60) as client:
                res = client.get(
                    f"https://{domain}/rest/api/3/search",
                    auth=auth,
                    params={"jql": jql, "startAt": start_at, "maxResults": 25, "fields": "summary,description,comment"},
                )
                res.raise_for_status()
                body = res.json()

            issues = body.get("issues") or []
            result.records_fetched += len(issues)

            for issue in issues:
                key = issue.get("key")
                fields = issue.get("fields") or {}
                summary = fields.get("summary") or key
                desc = fields.get("description")
                desc_text = _adf_to_text(desc) if isinstance(desc, dict) else str(desc or "")
                comments = []
                for c in (fields.get("comment") or {}).get("comments") or []:
                    comments.append(_adf_to_text(c.get("body")) if isinstance(c.get("body"), dict) else str(c.get("body") or ""))
                body_text = f"{desc_text}\n\n" + "\n".join(comments)

                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": str(key),
                        "interaction_type": "note",
                        "title": summary,
                        "body_text": body_text.strip(),
                        "raw_properties": issue,
                    },
                )
                if saved:
                    result.records_written += 1

            total = body.get("total", 0)
            next_start = start_at + len(issues)
            if next_start < total:
                result.cursor = {"start_at": next_start}
            else:
                result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("Jira sync failed for org %s", org_id)
            result.error = str(exc)

        return result


def _adf_to_text(node: Any) -> str:
    """Handles  adf to text logic for the surrounding Stoa workflow.

    Args:
        node (Any): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    if not isinstance(node, dict):
        return str(node or "")
    if node.get("type") == "text":
        return node.get("text") or ""
    parts = []
    for child in node.get("content") or []:
        parts.append(_adf_to_text(child))
    return " ".join(parts)
