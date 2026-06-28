"""Tier 4 agent tool: structured canonical record lookups."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from langchain_core.tools import StructuredTool

from stoa_core.agent.evidence import EvidenceHit, store_conversation_evidence
from stoa_core.db.supabase import get_supabase_admin


def build_crm_tools(org_id: str, conversation_id: str) -> list[StructuredTool]:
    def lookup_canonical_records(
        query: str,
        record_type: str = "all",
        limit: int = 10,
    ) -> str:
        """Look up CRM/support records by name, email, domain, or deal stage."""
        sb = get_supabase_admin()
        q = query.strip()
        lim = min(max(limit, 1), 25)
        hits: list[EvidenceHit] = []
        now = datetime.now(UTC).isoformat()

        if record_type in {"all", "accounts", "account"}:
            res = (
                sb.table("canonical_accounts")
                .select("id, name, domain, industry, lifecycle_stage")
                .eq("org_id", org_id)
                .or_(f"name.ilike.%{q}%,domain.ilike.%{q}%")
                .limit(lim)
                .execute()
            )
            for row in res.data or []:
                hits.append(
                    EvidenceHit(
                        id=str(row.get("id")),
                        title=str(row.get("name") or "Account"),
                        snippet=(
                            f"domain={row.get('domain')}; industry={row.get('industry')}; "
                            f"stage={row.get('lifecycle_stage')}"
                        ),
                        uri=f"canonical:account:{row.get('id')}",
                        provider="canonical",
                        source="canonical",
                        fetched_at=now,
                        entity_type="accounts",
                    )
                )

        if record_type in {"all", "contacts", "contact"}:
            res = (
                sb.table("canonical_contacts")
                .select("id, name, email, title")
                .eq("org_id", org_id)
                .or_(f"name.ilike.%{q}%,email.ilike.%{q}%")
                .limit(lim)
                .execute()
            )
            for row in res.data or []:
                hits.append(
                    EvidenceHit(
                        id=str(row.get("id")),
                        title=str(row.get("name") or row.get("email") or "Contact"),
                        snippet=f"email={row.get('email')}; title={row.get('title')}",
                        uri=f"canonical:contact:{row.get('id')}",
                        provider="canonical",
                        source="canonical",
                        fetched_at=now,
                        entity_type="contacts",
                    )
                )

        if record_type in {"all", "deals", "deal"}:
            res = (
                sb.table("canonical_deals")
                .select("id, name, amount, stage, close_date, is_won")
                .eq("org_id", org_id)
                .or_(f"name.ilike.%{q}%,stage.ilike.%{q}%")
                .order("amount", desc=True)
                .limit(lim)
                .execute()
            )
            for row in res.data or []:
                hits.append(
                    EvidenceHit(
                        id=str(row.get("id")),
                        title=str(row.get("name") or "Deal"),
                        snippet=(
                            f"amount={row.get('amount')}; stage={row.get('stage')}; "
                            f"close={row.get('close_date')}; won={row.get('is_won')}"
                        ),
                        uri=f"canonical:deal:{row.get('id')}",
                        provider="canonical",
                        source="canonical",
                        fetched_at=now,
                        entity_type="deals",
                    )
                )

        stored = store_conversation_evidence(
            org_id,
            conversation_id,
            source="canonical",
            query=q,
            hits=hits,
            entity_type=record_type,
        )
        return json.dumps(
            {
                "count": len(stored),
                "hits": [
                    {"title": h.title, "snippet": h.snippet[:300], "uri": h.uri}
                    for h in stored[:lim]
                ],
            },
            default=str,
        )

    return [StructuredTool.from_function(lookup_canonical_records)]
