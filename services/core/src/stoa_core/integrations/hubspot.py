"""
File: services/core/src/stoa_core/integrations/hubspot.py
Layer: Core Integration Connectors
Purpose: Implements hubspot behavior for the core integration connectors.
Dependencies: Next.js, stoa_core
"""


from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_account, upsert_contact, upsert_deal

logger = logging.getLogger(__name__)

HUBSPOT_SCOPES = [
    "crm.objects.contacts.read",
    "crm.objects.companies.read",
    "crm.objects.deals.read",
    "crm.schemas.contacts.read",
    "crm.schemas.companies.read",
    "crm.schemas.deals.read",
]

SOURCE = "hubspot"
MAX_PAGES = 50
PAGE_SIZE = 100


def _settings() -> Any:
    """Handles  settings logic for the surrounding Stoa workflow.

    Returns:
        Any: Result produced for the caller.
    """
    return get_settings()


@register_connector
class HubSpotConnector(BaseConnector):
    """Manage HubSpotConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "hubspot"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="hubspot",
            name="HubSpot",
            auth_type="oauth",
            description="Sync contacts, companies, and deals from HubSpot CRM.",
            scopes=HUBSPOT_SCOPES,
        )

    @classmethod
    def oauth_authorize_url(cls, state: str, redirect_uri: str) -> str:
        """Handles oauth authorize url logic for the surrounding Stoa workflow.

        Args:
            state (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.

        Returns:
            str: Result produced for the caller.
        """
        s = _settings()
        params = {
            "client_id": s.hubspot_client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(HUBSPOT_SCOPES),
            "state": state,
        }
        return f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        """Handles exchange oauth code logic for the surrounding Stoa workflow.

        Args:
            code (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        s = _settings()
        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": s.hubspot_client_id,
                    "client_secret": s.hubspot_client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            res.raise_for_status()
            data = res.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in"),
            "provider_metadata": {"hub_id": data.get("hub_id")},
        }

    @classmethod
    def _refresh_token(cls, credentials: dict[str, Any]) -> dict[str, Any]:
        """Handles  refresh token logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        refresh = credentials.get("refresh_token")
        if not refresh:
            return credentials
        s = _settings()
        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": s.hubspot_client_id,
                    "client_secret": s.hubspot_client_secret,
                    "refresh_token": refresh,
                },
            )
            if res.status_code >= 400:
                return credentials
            data = res.json()
        credentials["access_token"] = data["access_token"]
        if data.get("refresh_token"):
            credentials["refresh_token"] = data["refresh_token"]
        return credentials

    @classmethod
    def _headers(cls, credentials: dict[str, Any]) -> dict[str, str]:
        """Handles  headers logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.

        Returns:
            dict[str, str]: Result produced for the caller.
        """
        creds = cls._refresh_token(credentials)
        return {"Authorization": f"Bearer {creds['access_token']}"}

    @classmethod
    def _fetch_objects(
        cls,
        credentials: dict[str, Any],
        object_type: str,
        *,
        after: str | None = None,
        properties: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Handles  fetch objects logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.
            object_type (str): Input value used by this workflow step.
            after (str | None): Input value used by this workflow step.
            properties (list[str] | None): Input value used by this workflow step.

        Returns:
            tuple[list[dict[str, Any]], str | None]: Result produced for the caller.
        """
        params: dict[str, Any] = {"limit": PAGE_SIZE}
        if properties:
            params["properties"] = ",".join(properties)
        if after:
            params["after"] = after
        with httpx.Client(timeout=60) as client:
            res = client.get(
                f"https://api.hubapi.com/crm/v3/objects/{object_type}",
                headers=cls._headers(credentials),
                params=params,
            )
            res.raise_for_status()
            body = res.json()
        results = body.get("results") or []
        paging = body.get("paging") or {}
        next_after = (paging.get("next") or {}).get("after")
        return results, next_after

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
        result = SyncResult(cursor=dict(cursor))
        stage = cursor.get("stage") or "companies"
        after = cursor.get("after")
        pages_done = cursor.get("pages_done", 0)

        company_props = ["name", "domain", "industry", "numberofemployees", "country", "lifecyclestage"]
        contact_props = ["firstname", "lastname", "email", "jobtitle", "company"]
        deal_props = [
            "dealname",
            "amount",
            "dealstage",
            "pipeline",
            "closedate",
            "hs_is_closed_won",
            "closed_lost_reason",
            "hubspot_owner_id",
        ]

        stages = ["companies", "contacts", "deals"]
        if stage not in stages:
            stage = "companies"

        prop_map = {
            "companies": company_props,
            "contacts": contact_props,
            "deals": deal_props,
        }

        try:
            while pages_done < MAX_PAGES:
                objects, next_after = cls._fetch_objects(
                    credentials,
                    stage,
                    after=after,
                    properties=prop_map[stage],
                )
                result.records_fetched += len(objects)

                for obj in objects:
                    props = obj.get("properties") or {}
                    ext_id = str(obj.get("id"))
                    if stage == "companies":
                        row = {
                            "external_source": SOURCE,
                            "external_id": ext_id,
                            "name": props.get("name"),
                            "domain": props.get("domain"),
                            "industry": props.get("industry"),
                            "employee_count_range": _employee_range(props.get("numberofemployees")),
                            "country": props.get("country"),
                            "lifecycle_stage": props.get("lifecyclestage"),
                            "raw_properties": props,
                        }
                        if upsert_account(org_id, row):
                            result.records_written += 1
                    elif stage == "contacts":
                        name = " ".join(
                            p for p in [props.get("firstname"), props.get("lastname")] if p
                        ).strip()
                        row = {
                            "external_source": SOURCE,
                            "external_id": ext_id,
                            "email": props.get("email"),
                            "name": name or None,
                            "title": props.get("jobtitle"),
                            "raw_properties": props,
                        }
                        if upsert_contact(org_id, row):
                            result.records_written += 1
                    elif stage == "deals":
                        is_won = _parse_bool(props.get("hs_is_closed_won"))
                        row = {
                            "external_source": SOURCE,
                            "external_id": ext_id,
                            "name": props.get("dealname"),
                            "amount": _parse_amount(props.get("amount")),
                            "stage": props.get("dealstage"),
                            "pipeline": props.get("pipeline"),
                            "close_date": props.get("closedate"),
                            "is_won": is_won,
                            "is_closed": is_won is not None,
                            "loss_reason": props.get("closed_lost_reason"),
                            "raw_properties": props,
                        }
                        if upsert_deal(org_id, row):
                            result.records_written += 1

                pages_done += 1
                if next_after:
                    after = next_after
                    result.cursor = {"stage": stage, "after": after, "pages_done": pages_done}
                    time.sleep(0.15)
                    continue

                idx = stages.index(stage)
                if idx + 1 < len(stages):
                    stage = stages[idx + 1]
                    after = None
                    pages_done = 0
                    result.cursor = {"stage": stage, "after": None, "pages_done": 0}
                    continue
                result.cursor = {"stage": "done", "completed_at": time.time()}
                break

        except Exception as exc:
            logger.exception("HubSpot sync failed for org %s", org_id)
            result.error = str(exc)
            result.cursor = {"stage": stage, "after": after, "pages_done": pages_done}

        return result


def _employee_range(value: Any) -> str | None:
    """Handles  employee range logic for the surrounding Stoa workflow.

    Args:
        value (Any): Input value used by this workflow step.

    Returns:
        str | None: Result produced for the caller.
    """
    if value is None:
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return str(value)
    if n <= 10:
        return "1-10"
    if n <= 50:
        return "11-50"
    if n <= 200:
        return "51-200"
    if n <= 1000:
        return "201-1000"
    return "1000+"


def _parse_bool(value: Any) -> bool | None:
    """Handles  parse bool logic for the surrounding Stoa workflow.

    Args:
        value (Any): Input value used by this workflow step.

    Returns:
        bool | None: Result produced for the caller.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


def _parse_amount(value: Any) -> float | None:
    """Handles  parse amount logic for the surrounding Stoa workflow.

    Args:
        value (Any): Input value used by this workflow step.

    Returns:
        float | None: Result produced for the caller.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
