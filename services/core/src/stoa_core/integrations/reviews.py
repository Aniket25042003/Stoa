"""
File: services/core/src/stoa_core/integrations/reviews.py
Layer: Core Integration Connectors
Purpose: Implements reviews behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import guided_reviews_resources
from stoa_core.integrations.store import upsert_interaction

logger = logging.getLogger(__name__)

SOURCE = "reviews"
APIFY_ACTOR = "zen-studio/software-review-scraper"


@register_connector
class ReviewsConnector(BaseConnector):
    """Manage ReviewsConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "reviews"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="reviews",
            name="Product Reviews",
            auth_type="api_key",
            description="Import reviews from G2, Capterra, and TrustRadius using a product URL or name.",
            connection_mode="platform",
            resource_selection_mode="required",
            resource_kinds=["platform", "query"],
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
        return guided_reviews_resources()

    @classmethod
    def connect_with_credentials(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles connect with credentials logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        query = credentials.get("product_query", "").strip()
        platforms = credentials.get("platforms") or ["g2", "capterra", "trustradius"]
        return {
            "product_query": query,
            "provider_metadata": {
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
