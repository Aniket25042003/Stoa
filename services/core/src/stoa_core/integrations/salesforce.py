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
from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import upsert_account, upsert_contact, upsert_deal

logger = logging.getLogger(__name__)

SOURCE = "salesforce"


@register_connector
class SalesforceConnector(BaseConnector):
    """Manage SalesforceConnector behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    provider = "salesforce"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Handles provider info logic for the surrounding Stoa workflow.

        Returns:
            ProviderInfo: Result produced for the caller.
        """
        return ProviderInfo(
            id="salesforce",
            name="Salesforce",
            auth_type="oauth",
            description="Sync accounts, contacts, and opportunities from Salesforce.",
            scopes=["api", "refresh_token"],
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
        s = get_settings()
        params = {
            "response_type": "code",
            "client_id": s.salesforce_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"https://login.salesforce.com/services/oauth2/authorize?{urlencode(params)}"

    @classmethod
    def exchange_oauth_code(cls, code: str, redirect_uri: str) -> dict[str, Any]:
        """Handles exchange oauth code logic for the surrounding Stoa workflow.

        Args:
            code (str): Input value used by this workflow step.
            redirect_uri (str): Input value used by this workflow step.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        s = get_settings()
        with httpx.Client(timeout=30) as client:
            res = client.post(
                "https://login.salesforce.com/services/oauth2/token",
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
            "provider_metadata": {
                "instance_url": data.get("instance_url"),
            },
        }

    @classmethod
    def _query(cls, credentials: dict[str, Any], metadata: dict[str, Any], soql: str) -> list[dict[str, Any]]:
        """Handles  query logic for the surrounding Stoa workflow.

        Args:
            credentials (dict[str, Any]): Input value used by this workflow step.
            metadata (dict[str, Any]): Input value used by this workflow step.
            soql (str): Input value used by this workflow step.

        Returns:
            list[dict[str, Any]]: Result produced for the caller.
        """
        instance = metadata.get("instance_url") or credentials.get("instance_url")
        headers = {"Authorization": f"Bearer {credentials['access_token']}"}
        with httpx.Client(timeout=60) as client:
            res = client.get(
                f"{instance}/services/data/v59.0/query",
                headers=headers,
                params={"q": soql},
            )
            res.raise_for_status()
            return res.json().get("records") or []

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
        stage = cursor.get("stage") or "accounts"

        try:
            if stage == "accounts":
                records = cls._query(
                    credentials,
                    metadata,
                    "SELECT Id, Name, Website, Industry, NumberOfEmployees, BillingCountry FROM Account LIMIT 200",
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
                result.cursor = {"stage": "contacts"}

            elif stage == "contacts":
                records = cls._query(
                    credentials,
                    metadata,
                    "SELECT Id, FirstName, LastName, Email, Title, AccountId, LeadSource FROM Contact LIMIT 200",
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
                result.cursor = {"stage": "opportunities"}

            elif stage == "opportunities":
                records = cls._query(
                    credentials,
                    metadata,
                    "SELECT Id, Name, Amount, StageName, CloseDate, IsWon, IsClosed, LeadSource, CampaignId FROM Opportunity LIMIT 200",
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
                result.cursor = {"stage": "done"}

        except Exception as exc:
            logger.exception("Salesforce sync failed for org %s", org_id)
            result.error = str(exc)

        return result
