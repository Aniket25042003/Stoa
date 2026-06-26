"""
File: services/core/src/stoa_core/analytics/questions.py
Layer: Core Analytics
Purpose: Precomputed campaign analysis questions.
"""

from __future__ import annotations

CAMPAIGN_ANALYSIS_QUESTIONS: list[dict[str, str]] = [
    {
        "key": "top_converting_channels",
        "title": "Which channels drive conversions?",
        "question": (
            "Which marketing channels drive the most conversions? Rank channels with evidence."
        ),
    },
    {
        "key": "best_vs_worst_campaign",
        "title": "Why did our top campaign outperform?",
        "question": (
            "Compare our best-performing campaign to our worst. Why did the top campaign win?"
        ),
    },
    {
        "key": "audience_that_converts",
        "title": "Which audience segments convert?",
        "question": (
            "Which audience segments or industries convert best based on campaign and CRM data?"
        ),
    },
    {
        "key": "message_effectiveness",
        "title": "Which messages work?",
        "question": "Which campaign messaging themes correlate with conversions and pipeline?",
    },
]

CAMPAIGN_ANALYSIS_KINDS = [
    "product_analytics_summary",
    "campaign_asset",
    "campaign_metrics",
    "crm_deal",
    "crm_contact",
    "icp_profile",
]
