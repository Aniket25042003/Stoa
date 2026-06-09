from stoa_core.org.completeness import compute_completeness


def test_completeness_empty_org():
    result = compute_completeness({"name": "Acme", "profile": {}})
    assert result["percent"] < 100
    assert "documents" in result["missing"]
    assert result["ready_for_intelligence"] is False


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
    )
    assert result["percent"] == 100
    assert result["ready_for_intelligence"] is True
    assert result["ready_for_competitive"] is True
    assert result["ready_for_campaigns"] is True
