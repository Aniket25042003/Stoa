"""Structured CSV import connector."""

from __future__ import annotations

import csv
import io
import logging
import re
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

CSV_FIELD_DEFINITIONS: list[dict[str, Any]] = [
    {"key": "email", "label": "Email address", "group": "Contact", "aliases": ["email", "contact_email", "e_mail", "work_email"]},
    {"key": "name", "label": "Contact name", "group": "Contact", "aliases": ["name", "contact_name", "full_name", "contact"]},
    {"key": "title", "label": "Job title", "group": "Contact", "aliases": ["title", "job_title", "position", "job_role"]},
    {"key": "company", "label": "Company name", "group": "Company", "aliases": ["company", "account", "account_name", "organization", "company_name"]},
    {"key": "domain", "label": "Company domain", "group": "Company", "aliases": ["domain", "website", "company_domain", "company_website"]},
    {"key": "industry", "label": "Industry", "group": "Company", "aliases": ["industry", "sector", "vertical"]},
    {"key": "deal_name", "label": "Deal name", "group": "Deal", "aliases": ["deal_name", "deal", "opportunity", "opportunity_name"]},
    {"key": "deal_amount", "label": "Deal amount", "group": "Deal", "aliases": ["deal_amount", "amount", "value", "revenue", "deal_value"]},
    {"key": "deal_stage", "label": "Deal stage", "group": "Deal", "aliases": ["deal_stage", "stage", "pipeline_stage", "sales_stage"]},
    {"key": "won", "label": "Won / lost", "group": "Deal", "aliases": ["won", "is_won", "win", "closed_won", "deal_status"]},
    {"key": "loss_reason", "label": "Loss reason", "group": "Deal", "aliases": ["loss_reason", "lost_reason", "reason_lost", "closed_lost_reason"]},
    {"key": "transcript", "label": "Call transcript", "group": "Content", "aliases": ["transcript", "call_transcript", "conversation", "call_notes"]},
    {"key": "review", "label": "Customer review", "group": "Content", "aliases": ["review", "review_text", "feedback", "customer_review"]},
]

FIELD_ALIASES: dict[str, list[str]] = {row["key"]: row["aliases"] for row in CSV_FIELD_DEFINITIONS}


def _normalize_header(header: str) -> str:
    normalized = header.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def _header_tokens(norm_header: str) -> list[str]:
    return [token for token in norm_header.split("_") if token]


def _match_score(norm_header: str, alias: str) -> int:
    norm_alias = _normalize_header(alias)
    if not norm_header or not norm_alias:
        return 0
    if norm_header == norm_alias:
        return 100
    tokens = _header_tokens(norm_header)
    if norm_alias in tokens:
        return 85
    if len(norm_alias) >= 5 and norm_header.endswith(f"_{norm_alias}"):
        return 70
    if len(norm_alias) >= 5 and norm_header.startswith(f"{norm_alias}_"):
        return 65
    return 0


def detect_columns(headers: list[str]) -> dict[str, str | None]:
    mapping: dict[str, str | None] = {field: None for field in FIELD_ALIASES}
    if not headers:
        return mapping

    assignments: list[tuple[int, str, str]] = []
    for header in headers:
        norm = _normalize_header(header)
        if not norm:
            continue
        for field, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                score = _match_score(norm, alias)
                if score > 0:
                    assignments.append((score, field, header))

    assignments.sort(key=lambda item: (-item[0], item[1], item[2]))
    used_fields: set[str] = set()
    used_headers: set[str] = set()

    for score, field, header in assignments:
        if score < 65:
            continue
        if field in used_fields or header in used_headers:
            continue
        mapping[field] = header
        used_fields.add(field)
        used_headers.add(header)

    return mapping


def parse_csv_content(content: str, column_mapping: dict[str, str | None] | None = None) -> tuple[list[str], dict[str, str | None]]:
    reader = csv.DictReader(io.StringIO(content))
    headers = [h for h in (reader.fieldnames or []) if h and h.strip()]
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
