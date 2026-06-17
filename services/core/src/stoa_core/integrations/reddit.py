"""Reddit brand mention monitor."""

from __future__ import annotations

import logging
from datetime import UTC
from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "reddit"


@register_connector
class RedditConnector(BaseConnector):
    provider = "reddit"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="reddit",
            name="Reddit",
            auth_type="api_key",
            description="Monitor subreddits for brand and product mentions.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        query = credentials.get("search_query", "").strip()
        subreddits = credentials.get("subreddits") or []
        if not query:
            raise ValueError("Reddit search_query is required")
        return {
            "search_query": query,
            "provider_metadata": {
                "search_query": query,
                "subreddits": subreddits,
            },
        }

    @classmethod
    def _reddit_headers(cls) -> dict[str, str]:
        s = get_settings()
        return {
            "User-Agent": s.reddit_user_agent or "stoa-intelligence/1.0",
            "Authorization": f"Bearer {s.reddit_access_token}" if s.reddit_access_token else "",
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
        query = metadata.get("search_query") or credentials.get("search_query")
        subreddits = metadata.get("subreddits") or ["all"]
        after = cursor.get("after")

        if not get_settings().reddit_access_token:
            result.error = "REDDIT_ACCESS_TOKEN is not configured"
            return result

        try:
            sub = subreddits[0] if subreddits else "all"
            params: dict[str, Any] = {"q": query, "limit": 25, "sort": "new"}
            if after:
                params["after"] = after

            with httpx.Client(timeout=60) as client:
                res = client.get(
                    f"https://oauth.reddit.com/r/{sub}/search",
                    headers=cls._reddit_headers(),
                    params=params,
                )
                res.raise_for_status()
                body = res.json()

            posts = body.get("data", {}).get("children") or []
            result.records_fetched = len(posts)

            for child in posts:
                post = child.get("data") or {}
                post_id = post.get("id")
                if not post_id:
                    continue
                title = post.get("title") or f"Reddit post {post_id}"
                body_text = f"{post.get('selftext', '')}\n\nURL: https://reddit.com{post.get('permalink', '')}"
                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": post_id,
                        "interaction_type": "review",
                        "title": title,
                        "body_text": body_text.strip(),
                        "occurred_at": _ts(post.get("created_utc")),
                        "raw_properties": post,
                    },
                )
                if saved:
                    result.records_written += 1

            result.cursor = {
                "after": body.get("data", {}).get("after"),
                "stage": "done" if not body.get("data", {}).get("after") else "continue",
            }

        except Exception as exc:
            logger.exception("Reddit sync failed for org %s", org_id)
            result.error = str(exc)

        return result


def _ts(created_utc: Any) -> str | None:
    if created_utc is None:
        return None
    try:
        from datetime import datetime

        return datetime.fromtimestamp(float(created_utc), tz=UTC).isoformat()
    except (TypeError, ValueError):
        return None
