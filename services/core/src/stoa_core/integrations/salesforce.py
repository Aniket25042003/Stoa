"""
File: services/core/src/stoa_core/integrations/salesforce.py
Layer: Core Integration Connectors
Purpose: Implements salesforce behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.attribution import extract_attribution
from stoa_core.integrations.base import BaseConnector, ProviderInfo, ResourceListResult, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.resource_listers import list_salesforce_resources
from stoa_core.integrations.store import upsert_account, upsert_contact, upsert_deal

logger = logging.getLogger(__name__)

SOURCE = "salesforce"
MAX_PAGES = 50


def _login_host(environment: str | None) -> str:
    return "test.salesforce.com" if environment == "sandbox" else "login.salesforce.com"


@register_connector
class SalesforceConnector(BaseConnector):
    """Manage SalesforceConnector behavior within the Stoa application layer."""

    provider = "salesforce"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="salesforce",
            name="Salesforce",
            auth_type="oauth",
            description="Sync accounts, contacts, and opportunities from Salesforce.",
            scopes=["api", "refresh_token"],
            resource_selection_mode="required",
            resource_kinds=["object_type", "record_type"],
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
        return list_salesforce_resources(credentials, metadata)

    @classmethod
    def oauth_authorize_url(
        cls,
        state: str,
        redirect_uri: str,
        *,
        oauth_params: dict[str, Any] | None = None,
    ) -> str | None:
        s = get_settings()
        if not s.salesforce_client_id.strip():
            return None
        oauth_params = oauth_params or {}
        environment = oauth_params.get("environment", "production")
        params = {
            "response_type": "code",
            "client_id": s.salesforce_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        host = _login_host(environment)
        return f"https://{host}/services/oauth2/authorize?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(
        cls,
        code: str,
        redirect_uri: str,
        *,
        oauth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        s = get_settings()
        oauth_context = oauth_context or {}
        environment = oauth_context.get("environment", "production")
        host = _login_host(environment)
        with httpx.Client(timeout=30) as client:
            res = client.post(
                f"https://{host}/services/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": s.salesforce_client_id,
                    "client_secret": s.salesforce_client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            res.raise_for_status()
            data = res.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "instance_url": data.get("instance_url"),
            "provider_metadata": {
                "instance_url": data.get("instance_url"),
                "environment": environment,
            },
        }

    @classmethod
    def _query_all(
        cls,
        credentials: dict[str, Any],
        metadata: dict[str, Any],
        soql: str,
        *,
        next_url: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        instance = metadata.get("instance_url") or credentials.get("instance_url")
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}
        records: list[dict[str, Any]] = []
        url = next_url or f"{instance}/services/data/v59.0/query"
        params = None if next_url else {"q": soql}

        with httpx.Client(timeout=60) as client:
            for _ in range(MAX_PAGES):
                res = client.get(url, headers=headers, params=params)
                res.raise_for_status()
                body = res.json()
                records.extend(body.get("records") or [])
                if body.get("done"):
                    return records, None
                url = f"{instance}{body['nextRecordsUrl']}"
                params = None
        return records, url

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
        result = SyncResult(cursor=dict(cursor))
        metadata = connection.get("provider_metadata") or {}
        objects = metadata.get("objects") or ["Account", "Contact", "Opportunity"]
        stage = cursor.get("stage") or "accounts"
        stage_order = [
            ("accounts", "Account"),
            ("contacts", "Contact"),
            ("opportunities", "Opportunity"),
        ]
        allowed_stages = [s for s, obj in stage_order if obj in objects]
        if not allowed_stages:
            result.error = "No Salesforce objects selected — configure access first"
            return result
        if stage not in allowed_stages:
            stage = allowed_stages[0]
        next_url = cursor.get("next_url")

        try:
            if stage == "accounts" and "accounts" in allowed_stages:
                if next_url:
                    records, next_url = cls._query_all(credentials, metadata, "", next_url=next_url)
                else:
                    records, next_url = cls._query_all(
                        credentials,
                        metadata,
                        "SELECT Id, Name, Website, Industry, NumberOfEmployees, BillingCountry FROM Account",
                    )
                result.records_fetched += len(records)
                for rec in records:
                    saved = upsert_account(
                        org_id,
                        {
                            "external_source": SOURCE,
                            "external_id": rec["Id"],
                            "name": rec.get("Name"),
                            "domain": rec.get("Website"),
                            "industry": rec.get("Industry"),
                            "country": rec.get("BillingCountry"),
                            "raw_properties": rec,
                        },
                    )
                    if saved:
                        result.records_written += 1
                if next_url:
                    result.cursor = {"stage": "accounts", "next_url": next_url}
                else:
                    idx = allowed_stages.index("accounts")
                    result.cursor = {"stage": allowed_stages[idx + 1] if idx + 1 < len(allowed_stages) else "done"}

            elif stage == "contacts" and "contacts" in allowed_stages:
                if next_url:
                    records, next_url = cls._query_all(credentials, metadata, "", next_url=next_url)
                else:
                    records, next_url = cls._query_all(
                        credentials,
                        metadata,
                        "SELECT Id, FirstName, LastName, Email, Title, AccountId, LeadSource FROM Contact",
                    )
                result.records_fetched += len(records)
                for rec in records:
                    name = " ".join(p for p in [rec.get("FirstName"), rec.get("LastName")] if p)
                    attr = extract_attribution(rec, external_source=SOURCE)
                    saved = upsert_contact(
                        org_id,
                        {
                            "external_source": SOURCE,
                            "external_id": rec["Id"],
                            "email": rec.get("Email"),
                            "name": name or None,
                            "title": rec.get("Title"),
                            "raw_properties": rec,
                            **attr,
                        },
                    )
                    if saved:
                        result.records_written += 1
                if next_url:
                    result.cursor = {"stage": "contacts", "next_url": next_url}
                else:
                    idx = allowed_stages.index("contacts")
                    result.cursor = {"stage": allowed_stages[idx + 1] if idx + 1 < len(allowed_stages) else "done"}

            elif stage == "opportunities" and "opportunities" in allowed_stages:
                if next_url:
                    records, next_url = cls._query_all(credentials, metadata, "", next_url=next_url)
                else:
                    records, next_url = cls._query_all(
                        credentials,
                        metadata,
                        "SELECT Id, Name, Amount, StageName, CloseDate, IsWon, IsClosed, LeadSource, CampaignId FROM Opportunity",
                    )
                result.records_fetched += len(records)
                for rec in records:
                    attr = extract_attribution(rec, external_source=SOURCE)
                    saved = upsert_deal(
                        org_id,
                        {
                            "external_source": SOURCE,
                            "external_id": rec["Id"],
                            "name": rec.get("Name"),
                            "amount": rec.get("Amount"),
                            "stage": rec.get("StageName"),
                            "close_date": rec.get("CloseDate"),
                            "is_won": rec.get("IsWon"),
                            "is_closed": rec.get("IsClosed"),
                            "raw_properties": rec,
                            **attr,
                        },
                    )
                    if saved:
                        result.records_written += 1
                if next_url:
                    result.cursor = {"stage": "opportunities", "next_url": next_url}
                else:
                    result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("Salesforce sync failed for org %s", org_id)
            result.error = str(exc)

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
        objects = metadata.get("objects") or ["Account", "Contact", "Opportunity"]
        stage = entity_type or "opportunities"
        if stage in {"deals", "deal", "opportunity"}:
            stage = "opportunities"
        if stage == "accounts" and "Account" not in objects:
            stage = "opportunities" if "Opportunity" in objects else "accounts"

        hits: list[AgentSearchHit] = []
        q = query.replace("'", "\\'")[:120]

        if stage == "opportunities" and "Opportunity" in objects:
            soql = (
                "SELECT Id, Name, Amount, StageName, CloseDate, IsWon FROM Opportunity "
                f"WHERE Name LIKE '%{q}%' OR Id != null ORDER BY Amount DESC NULLS LAST LIMIT 15"
            )
            records, _ = cls._query_all(credentials, metadata, soql)
            for rec in records:
                amount = rec.get("Amount")
                hits.append(
                    agent_search_hit(
                        id=str(rec.get("Id")),
                        title=str(rec.get("Name") or "Opportunity"),
                        snippet=(
                            f"Amount={amount}; stage={rec.get('StageName')}; "
                            f"close={rec.get('CloseDate')}; won={rec.get('IsWon')}"
                        ),
                        provider=SOURCE,
                        entity_type="opportunities",
                    )
                )
        elif stage == "contacts" and "Contact" in objects:
            soql = (
                "SELECT Id, FirstName, LastName, Email, Title FROM Contact "
                f"WHERE Name LIKE '%{q}%' OR Email LIKE '%{q}%' LIMIT 15"
            )
            records, _ = cls._query_all(credentials, metadata, soql)
            for rec in records:
                name = " ".join(p for p in [rec.get("FirstName"), rec.get("LastName")] if p)
                hits.append(
                    agent_search_hit(
                        id=str(rec.get("Id")),
                        title=name or str(rec.get("Email") or "Contact"),
                        snippet=f"email={rec.get('Email')}; title={rec.get('Title')}",
                        provider=SOURCE,
                        entity_type="contacts",
                    )
                )
        elif "Account" in objects:
            soql = (
                "SELECT Id, Name, Website, Industry FROM Account "
                f"WHERE Name LIKE '%{q}%' OR Website LIKE '%{q}%' LIMIT 15"
            )
            records, _ = cls._query_all(credentials, metadata, soql)
            for rec in records:
                hits.append(
                    agent_search_hit(
                        id=str(rec.get("Id")),
                        title=str(rec.get("Name") or "Account"),
                        snippet=f"website={rec.get('Website')}; industry={rec.get('Industry')}",
                        provider=SOURCE,
                        entity_type="accounts",
                    )
                )
        return hits
