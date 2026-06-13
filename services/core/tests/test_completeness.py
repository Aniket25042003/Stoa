from stoa_core.org.completeness import compute_completeness


def test_completeness_empty_org():
    result = compute_completeness({"name": "Acme", "profile": {}})
    assert result["percent"] < 100
    assert "documents_or_integration" in result["missing"]
    assert result["ready_for_intelligence"] is False


def test_completeness_with_integration():
    result = compute_completeness(
        {"name": "Acme", "profile": {}},
        integration_count=1,
        canonical_deal_count=5,
    )
    assert result["ready_for_intelligence"] is True
    assert result["checks"]["has_structured_data"] is True


def test_completeness_with_data():
    result = compute_completeness(
        {
            "name": "Acme",
            "website_url": "https://acme.com",
            "industry": "SaaS",
            "profile": {
                "target_customers": "B2B marketers",
                "business_model": "Subscription",
                "stage": "Growth",
                "goals": "Expand ICP",
                "brand_voice": "Clear and direct",
            },
        },
        document_count=3,
        competitor_count=2,
        integration_count=1,
    )
    assert result["percent"] == 100
    assert result["ready_for_intelligence"] is True
    assert result["ready_for_competitive"] is True
    assert result["ready_for_campaigns"] is True
