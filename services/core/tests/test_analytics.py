"""Tests for campaign analysis aggregations."""

from __future__ import annotations

from stoa_core.analytics.aggregate import aggregate_channel_metrics
from stoa_core.analytics.compare import compare_campaigns


def test_aggregate_channel_metrics_empty(monkeypatch):
    monkeypatch.setattr(
        "stoa_core.analytics.aggregate.load_metric_facts",
        lambda org_id, dimension_type=None: [],
    )
    result = aggregate_channel_metrics("org-1")
    assert result["channels"] == []
    assert result["top_channel"] is None


def test_aggregate_channel_metrics_groups_channels(monkeypatch):
    facts = [
        {
            "dimension_type": "channel",
            "dimension_value": "Organic Search",
            "source": "ga4",
            "metrics": {"sessions": 100, "conversions": 10, "users": 80},
        },
        {
            "dimension_type": "channel",
            "dimension_value": "Paid Social",
            "source": "ga4",
            "metrics": {"sessions": 50, "conversions": 5, "users": 40},
        },
    ]
    monkeypatch.setattr(
        "stoa_core.analytics.aggregate.load_metric_facts",
        lambda org_id, dimension_type=None: facts if dimension_type == "channel" else facts,
    )
    result = aggregate_channel_metrics("org-1")
    assert len(result["channels"]) == 2
    assert result["top_channel"]["channel"] == "Organic Search"
    assert result["top_channel"]["conversion_rate_percent"] == 10.0


def test_compare_campaigns(monkeypatch):
    monkeypatch.setattr(
        "stoa_core.analytics.compare.aggregate_campaign_metrics",
        lambda org_id: {
            "campaigns": [
                {"campaign": "A", "sessions": 100, "conversions": 20},
                {"campaign": "B", "sessions": 80, "conversions": 5},
            ],
        },
    )
    result = compare_campaigns("org-1", "A", "B")
    assert result["found_both"] is True
    assert result["delta_conversions"] == 15
