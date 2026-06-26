"""
File: services/core/src/stoa_core/analytics/__init__.py
Layer: Core Analytics
Purpose: Campaign performance analytics — structured metrics and precomputed insights.
"""

from stoa_core.analytics.aggregate import aggregate_campaign_metrics, aggregate_channel_metrics
from stoa_core.analytics.compare import compare_campaigns

__all__ = [
    "aggregate_channel_metrics",
    "aggregate_campaign_metrics",
    "compare_campaigns",
]
