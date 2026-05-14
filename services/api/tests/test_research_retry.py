from __future__ import annotations

from gtm_agents.autonomy import revise_research_calls_for_retry, validate_research_calls


def test_zero_result_crawl_retry_switches_to_broad_web_search() -> None:
    call = {
        "tool_name": "crawl_search_results",
        "arguments": {
            "query": '"seed stage B2B founder" "GTM challenges" site:reddit.com OR site:news.ycombinator.com',
            "product_context": "AI GTM workspace",
            "max_results": 3,
        },
        "reason": "Find forum pain points.",
    }
    revised = revise_research_calls_for_retry(
        [call],
        {"product_name": "SignalForge", "target_customers": "seed-stage B2B founders"},
        {"items": [], "warnings": []},
        {"issues": ["The search query returned zero results."]},
        {"issues": ["No Results Found"]},
    )

    assert len(revised) == 1
    assert revised[0]["tool_name"] == "web_research"
    assert "site:" not in revised[0]["arguments"]["query"]
    assert revised[0]["arguments"]["max_results"] >= 5


def test_competitor_retry_splits_known_competitors() -> None:
    call = {
        "tool_name": "competitor_research",
        "arguments": {
            "query": "Clay.com and Regie.ai GTM strategy",
            "product_context": "AI GTM workspace",
            "max_results": 5,
        },
        "reason": "Compare competitors.",
    }
    revised = revise_research_calls_for_retry(
        [call],
        {"known_competitors": ["Clay.com", "Regie.ai"]},
        {"items": [{"source_url": "https://clay.com", "title": "Clay"}], "warnings": []},
        {"issues": ["No information was gathered for Regie.ai."]},
        {"issues": ["Split competitors into separate searches."]},
    )

    assert [c["tool_name"] for c in revised] == ["competitor_research", "competitor_research"]
    assert "Clay.com" in revised[0]["arguments"]["query"]
    assert "Regie.ai" in revised[1]["arguments"]["query"]


def test_planner_guardrail_rewrites_narrow_crawl_query() -> None:
    calls = [
        {
            "tool_name": "crawl_search_results",
            "arguments": {
                "query": '"seed stage B2B founder" "GTM challenges" site:reddit.com OR site:news.ycombinator.com',
                "max_results": 9,
                "max_pages_per_result": 5,
            },
        }
    ]
    validated, notes = validate_research_calls(calls, {"product_name": "SignalForge"})

    assert validated[0]["tool_name"] == "web_research"
    assert notes
