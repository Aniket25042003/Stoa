"""G2/Capterra/TrustRadius reviews via Apify."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "reviews"
APIFY_ACTOR = "zen-studio/software-review-scraper"


@register_connector
class ReviewsConnector(BaseConnector):
    provider = "reviews"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="reviews",
            name="Product Reviews",
            auth_type="api_key",
            description="Import reviews from G2, Capterra, and TrustRadius using a product URL or name.",
        )

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        query = credentials.get("product_query", "").strip()
        if not query:
            raise ValueError("Product URL or name is required for review import")
        platforms = credentials.get("platforms") or ["g2", "capterra", "trustradius"]
        return {
            "product_query": query,
            "provider_metadata": {
                "product_query": query,
                "platforms": platforms,
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

        query = metadata.get("product_query") or credentials.get("product_query")
        platforms = metadata.get("platforms") or ["g2", "capterra", "trustradius"]
        max_results = int(metadata.get("max_results") or 50)

        try:
            actor_id = APIFY_ACTOR.replace("/", "~")
            url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
            with httpx.Client(timeout=300) as client:
                res = client.post(
                    url,
                    params={"token": token},
                    json={
                        "query": query,
                        "platforms": platforms,
                        "maxResults": max_results,
                    },
                )
                res.raise_for_status()
                items = res.json()

            if not isinstance(items, list):
                items = []

            result.records_fetched = len(items)
            for idx, item in enumerate(items):
                review_id = str(item.get("id") or item.get("reviewId") or f"{idx}")
                platform = item.get("platform") or "review"
                title = item.get("title") or item.get("headline") or f"Review on {platform}"
                body_parts = []
                if item.get("pros"):
                    body_parts.append(f"Pros: {item['pros']}")
                if item.get("cons"):
                    body_parts.append(f"Cons: {item['cons']}")
                if item.get("text"):
                    body_parts.append(item["text"])
                if item.get("reviewText"):
                    body_parts.append(item["reviewText"])
                body = "\n".join(body_parts) or str(item)
                rating = item.get("rating") or item.get("stars")

                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": f"{platform}:{review_id}",
                        "interaction_type": "review",
                        "title": title,
                        "body_text": body,
                        "raw_properties": {**item, "rating": rating, "platform": platform},
                    },
                )
                if saved:
                    result.records_written += 1

            result.cursor = {"stage": "done", "review_count": result.records_written}

        except Exception as exc:
            logger.exception("Reviews sync failed for org %s", org_id)
            result.error = str(exc)

        return result
