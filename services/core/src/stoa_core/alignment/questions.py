"""
File: services/core/src/stoa_core/alignment/questions.py
Layer: Core Alignment
Purpose: Precomputed alignment questions.
"""

from __future__ import annotations

ALIGNMENT_QUESTIONS: list[dict[str, str]] = [
    {
        "key": "leads_that_convert",
        "title": "Which leads convert?",
        "question": (
            "Which lead sources and segments have the highest close rate? Use CRM evidence."
        ),
    },
    {
        "key": "campaigns_driving_revenue",
        "title": "Which campaigns drive revenue?",
        "question": (
            "Which marketing campaigns or UTM campaigns are associated with won deal revenue?"
        ),
    },
    {
        "key": "deal_stall_points",
        "title": "Where do deals stall?",
        "question": "At which pipeline stages do deals stall longest? What patterns appear?",
    },
    {
        "key": "marketing_sales_friction",
        "title": "Marketing vs sales friction",
        "question": (
            "What evidence explains tension between marketing and sales — "
            "lead quality, follow-up gaps, objections, or loss reasons?"
        ),
    },
]

ALIGNMENT_KINDS = [
    "crm_contact",
    "crm_deal",
    "call_transcript",
    "alignment_summary",
    "campaign_metrics",
    "icp_profile",
]
