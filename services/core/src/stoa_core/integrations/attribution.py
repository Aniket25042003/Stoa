"""
File: services/core/src/stoa_core/integrations/attribution.py
Layer: Core Integration Connectors
Purpose: Map CRM raw properties to canonical attribution columns.
"""

from __future__ import annotations

from typing import Any


def extract_attribution(props: dict[str, Any], *, external_source: str) -> dict[str, str | None]:
    """Extract lead_source and UTM fields from CRM raw properties."""
    if external_source == "hubspot":
        lead = (
            props.get("hs_analytics_source")
            or props.get("hs_latest_source")
            or props.get("hs_analytics_source_data_1")
        )
        utm_campaign = props.get("hs_analytics_source_data_2") or props.get("utm_campaign")
        utm_source = props.get("utm_source") or props.get("hs_analytics_source_data_1")
        utm_medium = props.get("utm_medium")
        return {
            "lead_source": _str(lead),
            "utm_campaign": _str(utm_campaign),
            "utm_source": _str(utm_source),
            "utm_medium": _str(utm_medium),
        }
    if external_source == "salesforce":
        return {
            "lead_source": _str(props.get("LeadSource")),
            "utm_campaign": _str(props.get("UTM_Campaign__c") or props.get("CampaignId")),
            "utm_source": _str(props.get("UTM_Source__c")),
            "utm_medium": _str(props.get("UTM_Medium__c")),
        }
    return {
        "lead_source": _str(props.get("lead_source") or props.get("source")),
        "utm_campaign": _str(props.get("utm_campaign")),
        "utm_source": _str(props.get("utm_source")),
        "utm_medium": _str(props.get("utm_medium")),
    }


def _str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value).strip() or None
