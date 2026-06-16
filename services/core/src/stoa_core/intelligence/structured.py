"""SQL aggregations on canonical CRM data for ICP enrichment."""

from __future__ import annotations

from collections import Counter
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


def aggregate_crm_stats(org_id: str) -> dict[str, Any]:
    sb = get_supabase_admin()

    accounts_res = (
        sb.table("canonical_accounts")
        .select("id, industry, employee_count_range, lifecycle_stage")
        .eq("org_id", org_id)
        .limit(500)
        .execute()
    )
    deals_res = (
        sb.table("canonical_deals")
        .select("amount, stage, is_won, is_closed, loss_reason, account_id")
        .eq("org_id", org_id)
        .limit(500)
        .execute()
    )
    contacts_res = (
        sb.table("canonical_contacts").select("title").eq("org_id", org_id).limit(500).execute()
    )

    accounts = accounts_res.data or []
    deals = deals_res.data or []
    contacts = contacts_res.data or []

    industries = Counter(a.get("industry") for a in accounts if a.get("industry"))
    sizes = Counter(
        a.get("employee_count_range") for a in accounts if a.get("employee_count_range")
    )
    titles = Counter(c.get("title") for c in contacts if c.get("title"))

    account_industry = {a.get("id"): a.get("industry") for a in accounts if a.get("id")}

    won = [d for d in deals if d.get("is_won") is True]
    lost = [d for d in deals if d.get("is_closed") is True and d.get("is_won") is False]
    win_rate = round(len(won) / len(deals) * 100, 1) if deals else None

    amounts = [float(d["amount"]) for d in deals if d.get("amount") is not None]
    median_deal = sorted(amounts)[len(amounts) // 2] if amounts else None

    loss_reasons = Counter(d.get("loss_reason") for d in lost if d.get("loss_reason"))

    deal_industries = Counter()
    for d in deals:
        aid = d.get("account_id")
        ind = account_industry.get(aid) if aid else None
        if ind:
            deal_industries[ind] += 1

    return {
        "total_accounts": len(accounts),
        "total_contacts": len(contacts),
        "total_deals": len(deals),
        "win_rate_percent": win_rate,
        "median_deal_amount": median_deal,
        "top_industries": [{"name": k, "count": v} for k, v in industries.most_common(5)],
        "top_company_sizes": [{"range": k, "count": v} for k, v in sizes.most_common(5)],
        "top_titles": [{"title": k, "count": v} for k, v in titles.most_common(8)],
        "top_loss_reasons": [{"reason": k, "count": v} for k, v in loss_reasons.most_common(5)],
        "deals_by_industry": [
            {"industry": k, "count": v} for k, v in deal_industries.most_common(5)
        ],
    }
