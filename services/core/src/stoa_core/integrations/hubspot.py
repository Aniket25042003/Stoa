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
from stoa_core.integrations.attribution import extract_attribution
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_hubspot_resources
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
            resource_selection_mode="required",
            resource_kinds=["object_type", "pipeline"],
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
        return list_hubspot_resources(credentials)

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str:
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
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
        metadata = connection.get("provider_metadata") or {}
        object_types = metadata.get("object_types") or ["companies", "contacts", "deals"]
        pipeline_ids = {str(p) for p in (metadata.get("pipeline_ids") or [])}
        stage = cursor.get("stage") or "companies"
        after = cursor.get("after")
        pages_done = cursor.get("pages_done", 0)

        company_props = ["name", "domain", "industry", "numberofemployees", "country", "lifecyclestage"]
        contact_props = [
            "firstname", "lastname", "email", "jobtitle", "company",
            "hs_analytics_source", "hs_analytics_source_data_1",
            "hs_analytics_source_data_2", "hs_latest_source",
            "utm_campaign", "utm_source", "utm_medium",
        ]
        deal_props = [
            "dealname",
            "amount",
            "dealstage",
            "pipeline",
            "closedate",
            "hs_is_closed_won",
            "closed_lost_reason",
            "hubspot_owner_id",
            "hs_analytics_source",
        ]

        stages = [s for s in ["companies", "contacts", "deals"] if s in object_types]
        if not stages:
            result.error = "No HubSpot object types selected — configure access first"
            return result
        if stage not in stages:
            stage = stages[0]

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
                        attr = extract_attribution(props, external_source=SOURCE)
                        row = {
                            "external_source": SOURCE,
                            "external_id": ext_id,
                            "email": props.get("email"),
                            "name": name or None,
                            "title": props.get("jobtitle"),
                            "raw_properties": props,
                            **attr,
                        }
                        if upsert_contact(org_id, row):
                            result.records_written += 1
                    elif stage == "deals":
                        if pipeline_ids and str(props.get("pipeline")) not in pipeline_ids:
                            continue
                        is_won = _parse_bool(props.get("hs_is_closed_won"))
                        attr = extract_attribution(props, external_source=SOURCE)
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
                            **attr,
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

    @classmethod
    def supports_agent_search(cls) -> bool:
        return True

    @classmethod
    def agent_search(
        cls,
        org_id: str,
        connection: dict[str, Any],
        *,
        credentials: dict[str, Any],
        query: str,
        entity_type: str | None = None,
    ) -> list:
        from stoa_core.integrations.agent_search import agent_search_hit
        from stoa_core.integrations.base import AgentSearchHit

        metadata = connection.get("provider_metadata") or {}
        object_types = metadata.get("object_types") or ["companies", "contacts", "deals"]
        stage = entity_type or ("deals" if "deals" in object_types else object_types[0])
        if stage not in object_types:
            stage = object_types[0]

        deal_props = [
            "dealname", "amount", "dealstage", "pipeline", "closedate", "hs_is_closed_won",
        ]
        contact_props = ["firstname", "lastname", "email", "jobtitle", "company"]
        company_props = ["name", "domain", "industry"]
        prop_map = {
            "deals": deal_props,
            "contacts": contact_props,
            "companies": company_props,
        }
        objects, _ = cls._fetch_objects(
            credentials,
            stage,
            properties=prop_map.get(stage, deal_props),
        )
        q_lower = query.strip().lower()
        hits: list[AgentSearchHit] = []

        if stage == "deals":
            ranked = []
            for obj in objects:
                props = obj.get("properties") or {}
                amount = _parse_amount(props.get("amount")) or 0.0
                ranked.append((amount, obj, props))
            ranked.sort(key=lambda x: x[0], reverse=True)
            for amount, obj, props in ranked[:12]:
                name = props.get("dealname") or f"Deal {obj.get('id')}"
                snippet = (
                    f"Amount={amount}; stage={props.get('dealstage')}; "
                    f"close={props.get('closedate')}; won={props.get('hs_is_closed_won')}"
                )
                hits.append(
                    agent_search_hit(
                        id=str(obj.get("id")),
                        title=str(name),
                        snippet=snippet,
                        provider=SOURCE,
                        entity_type=stage,
                    )
                )
        else:
            for obj in objects[:40]:
                props = obj.get("properties") or {}
                if stage == "contacts":
                    name = " ".join(
                        p for p in [props.get("firstname"), props.get("lastname")] if p
                    ).strip()
                    hay = f"{name} {props.get('email') or ''} {props.get('company') or ''}".lower()
                    if q_lower and q_lower not in hay:
                        continue
                    title = name or props.get("email") or f"Contact {obj.get('id')}"
                    snippet = f"email={props.get('email')}; title={props.get('jobtitle')}"
                else:
                    name = props.get("name") or f"Company {obj.get('id')}"
                    hay = f"{name} {props.get('domain') or ''}".lower()
                    if q_lower and q_lower not in hay:
                        continue
                    title = str(name)
                    snippet = f"domain={props.get('domain')}; industry={props.get('industry')}"
                hits.append(
                    agent_search_hit(
                        id=str(obj.get("id")),
                        title=title,
                        snippet=snippet,
                        provider=SOURCE,
                        entity_type=stage,
                    )
                )
                if len(hits) >= 12:
                    break
        return hits


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
