"""Structured CSV import connector."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from stoa_core.integrations.base import BaseConnector, ProviderInfo, SyncResult
from stoa_core.integrations.registry import register_connector
from stoa_core.integrations.store import (
    upsert_account,
    upsert_contact,
    upsert_deal,
    upsert_interaction,
)

logger = logging.getLogger(__name__)

SOURCE = "csv_structured"

FIELD_ALIASES: dict[str, list[str]] = {
    "email": ["email", "contact_email", "e-mail"],
    "name": ["name", "contact_name", "full_name", "contact"],
    "title": ["title", "job_title", "role", "position"],
    "company": ["company", "account", "account_name", "organization"],
    "domain": ["domain", "website", "company_domain"],
    "industry": ["industry", "sector"],
    "deal_name": ["deal_name", "deal", "opportunity", "opportunity_name"],
    "deal_amount": ["deal_amount", "amount", "value", "revenue"],
    "deal_stage": ["deal_stage", "stage", "pipeline_stage"],
    "won": ["won", "is_won", "win", "closed_won"],
    "loss_reason": ["loss_reason", "lost_reason", "reason_lost"],
    "transcript": ["transcript", "call_transcript", "conversation", "body"],
    "review": ["review", "review_text", "feedback"],
}


def detect_columns(headers: list[str]) -> dict[str, str | None]:
    normalized = {h: h.strip().lower().replace(" ", "_") for h in headers}
    mapping: dict[str, str | None] = {}
    for field, aliases in FIELD_ALIASES.items():
        mapping[field] = None
        for header, norm in normalized.items():
            if norm in aliases:
                mapping[field] = header
                break
    return mapping


def parse_csv_content(content: str, column_mapping: dict[str, str | None] | None = None) -> tuple[list[str], dict[str, str | None]]:
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    mapping = column_mapping or detect_columns(headers)
    return headers, mapping


@register_connector
class CsvStructuredConnector(BaseConnector):
    provider = "csv_structured"

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="csv_structured",
            name="Structured CSV",
            auth_type="upload",
            description="Import contacts, deals, and transcripts from a CSV file with column mapping.",
        )

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
        csv_content = credentials.get("csv_content") or ""
        mapping = credentials.get("column_mapping") or {}
        if not csv_content.strip():
            result.error = "No CSV content provided"
            return result

        reader = csv.DictReader(io.StringIO(csv_content))
        companies_seen: dict[str, str] = {}

        for row in reader:
            result.records_fetched += 1
            company_name = _cell(row, mapping.get("company"))
            domain = _cell(row, mapping.get("domain"))
            account_id = None

            if company_name or domain:
                key = (company_name or domain or "").lower()
                if key and key not in companies_seen:
                    saved = upsert_account(
                        org_id,
                        {
                            "external_source": SOURCE,
                            "external_id": key,
                            "name": company_name,
                            "domain": domain,
                            "industry": _cell(row, mapping.get("industry")),
                            "raw_properties": dict(row),
                        },
                    )
                    if saved:
                        companies_seen[key] = saved["id"]
                        result.records_written += 1
                account_id = companies_seen.get(key)

            email = _cell(row, mapping.get("email"))
            name = _cell(row, mapping.get("name"))
            if email or name:
                ext_id = email or f"{name}:{company_name}"
                saved = upsert_contact(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": ext_id,
                        "account_id": account_id,
                        "email": email,
                        "name": name,
                        "title": _cell(row, mapping.get("title")),
                        "raw_properties": dict(row),
                    },
                )
                if saved:
                    result.records_written += 1

            deal_name = _cell(row, mapping.get("deal_name"))
            if deal_name:
                amount_raw = _cell(row, mapping.get("deal_amount"))
                won_raw = _cell(row, mapping.get("won"))
                saved = upsert_deal(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": f"{deal_name}:{company_name or email}",
                        "account_id": account_id,
                        "name": deal_name,
                        "amount": _parse_float(amount_raw),
                        "stage": _cell(row, mapping.get("deal_stage")),
                        "is_won": _parse_won(won_raw),
                        "loss_reason": _cell(row, mapping.get("loss_reason")),
                        "raw_properties": dict(row),
                    },
                )
                if saved:
                    result.records_written += 1

            transcript = _cell(row, mapping.get("transcript"))
            review = _cell(row, mapping.get("review"))
            body = transcript or review
            if body:
                itype = "call_transcript" if transcript else "review"
                title = deal_name or company_name or f"Row {result.records_fetched}"
                saved = upsert_interaction(
                    org_id,
                    {
                        "external_source": SOURCE,
                        "external_id": f"row:{result.records_fetched}:{title[:40]}",
                        "interaction_type": itype,
                        "account_id": account_id,
                        "title": title,
                        "body_text": body,
                        "raw_properties": dict(row),
                    },
                )
                if saved:
                    result.records_written += 1

        result.cursor = {"completed": True}
        return result


def _cell(row: dict[str, str], column: str | None) -> str | None:
    if not column:
        return None
    val = row.get(column)
    if val is None:
        return None
    stripped = str(val).strip()
    return stripped or None


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace(",", "").replace("$", ""))
    except ValueError:
        return None


def _parse_won(value: str | None) -> bool | None:
    if not value:
        return None
    lower = value.lower()
    if lower in {"won", "true", "yes", "1", "closed won"}:
        return True
    if lower in {"lost", "false", "no", "0", "closed lost"}:
        return False
    return None
