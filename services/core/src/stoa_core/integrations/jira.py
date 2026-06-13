"""Jira issues connector (KB enrichment)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "jira"


@register_connector
class JiraConnector(BaseConnector):
    provider = "jira"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="jira",
            name="Jira",
            auth_type="api_key",
            description="Import Jira issues and comments as customer feedback signals.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        domain = credentials.get("domain", "").strip().rstrip("/")
        email = credentials.get("email", "").strip()
        api_token = credentials.get("api_token", "").strip()
        jql = credentials.get("jql", "ORDER BY updated DESC")
        if not domain or not email or not api_token:
            raise ValueError("Jira domain, email, and api_token are required")
        return {
            "domain": domain,
            "email": email,
            "api_token": api_token,
            "provider_metadata": {"domain": domain, "jql": jql},
        }

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
        result = SyncResult()
        metadata = connection.get("provider_metadata") or {}
        domain = metadata.get("domain") or credentials.get("domain")
        jql = metadata.get("jql") or "ORDER BY updated DESC"
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
    if not isinstance(node, dict):
        return str(node or "")
    if node.get("type") == "text":
        return node.get("text") or ""
    parts = []
    for child in node.get("content") or []:
        parts.append(_adf_to_text(child))
    return " ".join(parts)
