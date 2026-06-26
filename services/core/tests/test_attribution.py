"""Tests for attribution field extraction."""

from __future__ import annotations

from stoa_core.integrations.attribution import extract_attribution


def test_hubspot_attribution():
    props = {
        "hs_analytics_source": "ORGANIC_SEARCH",
        "hs_analytics_source_data_1": "google",
        "hs_analytics_source_data_2": "spring-campaign",
    }
    result = extract_attribution(props, external_source="hubspot")
    assert result["lead_source"] == "ORGANIC_SEARCH"
    assert result["utm_campaign"] == "spring-campaign"
    assert result["utm_source"] == "google"


def test_salesforce_attribution():
    props = {"LeadSource": "Web", "CampaignId": "701xx", "UTM_Source__c": "linkedin"}
    result = extract_attribution(props, external_source="salesforce")
    assert result["lead_source"] == "Web"
    assert result["utm_campaign"] == "701xx"
    assert result["utm_source"] == "linkedin"
