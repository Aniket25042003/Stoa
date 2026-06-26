"""
File: services/core/src/stoa_core/integrations/reddit.py
Layer: Core Integration Connectors
Purpose: Implements reddit behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import guided_reddit_subreddits
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "reddit"
APIFY_ACTOR = "clearpath/reddit-search-scraper"


@register_connector
class RedditConnector(BaseConnector):
    """Monitor Reddit mentions via Apify (platform-managed APIFY_API_TOKEN)."""

    provider = "reddit"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="reddit",
            name="Reddit",
            auth_type="api_key",
            description="Monitor subreddits for brand and product mentions.",
            connection_mode="platform",
            resource_selection_mode="required",
            resource_kinds=["subreddit", "query"],
        )

    @classmethod
    def list_discoverable_resources(
        cls,
        *,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        cursor: str | None = None,
        query: str | None = None,
    ) -> ResourceListResult:
        return guided_reddit_subreddits()

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        query = credentials.get("search_query", "").strip()
        subreddits = credentials.get("subreddits") or []
        return {
            "search_query": query,
            "provider_metadata": {
                "subreddits": subreddits,
                "max_results": credentials.get("max_results", 50),
            },
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
        token = get_settings().apify_api_token
        if not token:
            result.error = "APIFY_API_TOKEN is not configured"
            return result

        query = metadata.get("search_query") or credentials.get("search_query")
        subreddits = metadata.get("subreddits") or []
        max_results = int(metadata.get("max_results") or 50)

        try:
            actor_id = APIFY_ACTOR.replace("/", "~")
            url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
            payload: dict[str, Any] = {
                "query": query,
                "maxResults": max_results,
                "sort": "new",
                "contentType": "posts",
            }
            if subreddits:
                if len(subreddits) == 1:
                    payload["subreddit"] = str(subreddits[0]).removeprefix("r/").strip()
                else:
                    payload["subreddits"] = [
                        str(s).removeprefix("r/").strip() for s in subreddits if str(s).strip()
                    ]

            with httpx.Client(timeout=300) as client:
                res = client.post(url, params={"token": token}, json=payload)
                res.raise_for_status()
                items = res.json()

            if not isinstance(items, list):
                items = []

            result.records_fetched = len(items)
            for idx, item in enumerate(items):
                post_id = str(
                    item.get("id")
                    or item.get("postId")
                    or item.get("post_id")
                    or item.get("permalink")
                    or idx
                )
                title = item.get("title") or item.get("postTitle") or f"Reddit post {post_id}"
                body_parts = []
                for key in ("selftext", "body", "text", "postBody"):
                    if item.get(key):
                        body_parts.append(str(item[key]))
                permalink = item.get("permalink") or item.get("url") or ""
                if permalink and not str(permalink).startswith("http"):
                    permalink = f"https://reddit.com{permalink}"
                if permalink:
                    body_parts.append(f"URL: {permalink}")
                body_text = "\n\n".join(body_parts).strip() or str(item)

                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": post_id,
                        "interaction_type": "review",
                        "title": title,
                        "body_text": body_text,
                        "occurred_at": _parse_occurred_at(item),
                        "raw_properties": item,
                    },
                )
                if saved:
                    result.records_written += 1

            result.cursor = {"stage": "done", "post_count": result.records_written}

        except Exception as exc:
            logger.exception("Reddit sync failed for org %s", org_id)
            result.error = str(exc)

        return result


def _parse_occurred_at(item: dict[str, Any]) -> str | None:
    for key in ("createdAt", "created_utc", "createdUtc", "timestamp", "date"):
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, int | float):
            try:
                return datetime.fromtimestamp(float(value), tz=UTC).isoformat()
            except (TypeError, ValueError, OSError):
                continue
        if isinstance(value, str) and value.strip():
            return value
    return None
