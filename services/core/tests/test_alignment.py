"""Tests for sales–marketing alignment aggregations."""

from __future__ import annotations

from stoa_core.alignment.aggregate import aggregate_campaign_revenue, aggregate_lead_conversion
from stoa_core.alignment.stall import aggregate_stall_points


def test_aggregate_lead_conversion_empty(monkeypatch):
    monkeypatch.setattr("stoa_core.alignment.aggregate._load_contacts", lambda org_id: [])
    monkeypatch.setattr("stoa_core.alignment.aggregate._load_deals", lambda org_id: [])
    result = aggregate_lead_conversion("org-1")
    assert result["by_source"] == []


def test_aggregate_lead_conversion_by_source(monkeypatch):
    monkeypatch.setattr(
        "stoa_core.alignment.aggregate._load_contacts",
        lambda org_id: [
            {"id": "c1", "lead_source": "Inbound", "utm_campaign": None, "account_id": "a1"},
        ],
    )
    monkeypatch.setattr(
        "stoa_core.alignment.aggregate._load_deals",
        lambda org_id: [
            {
                "account_id": "a1",
                "lead_source": "Inbound",
                "utm_campaign": None,
                "is_won": True,
                "is_closed": True,
                "amount": 10000,
            },
        ],
    )
    result = aggregate_lead_conversion("org-1")
    assert len(result["by_source"]) >= 1
    assert result["by_source"][0]["source"] == "Inbound"
    assert result["by_source"][0]["won"] == 1


def test_aggregate_campaign_revenue(monkeypatch):
    monkeypatch.setattr(
        "stoa_core.alignment.aggregate._load_deals",
        lambda org_id: [
            {"utm_campaign": "spring-launch", "is_won": True, "amount": 5000},
            {"utm_campaign": "spring-launch", "is_won": True, "amount": 3000},
        ],
    )
    result = aggregate_campaign_revenue("org-1")
    assert result["top_campaign"]["campaign"] == "spring-launch"
    assert result["top_campaign"]["revenue"] == 8000


def test_aggregate_stall_points_empty(monkeypatch):
    class FakeRes:
        data = []

    class FakeTable:
        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def execute(self):
            return FakeRes()

    class FakeSb:
        def table(self, name):
            return FakeTable()

    monkeypatch.setattr("stoa_core.alignment.stall.get_supabase_admin", lambda: FakeSb())
    result = aggregate_stall_points("org-1")
    assert result["top_stall_stages"] == []
