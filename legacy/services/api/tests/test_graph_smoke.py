def test_graph_invokes(monkeypatch) -> None:
    monkeypatch.setenv("GTM_DISABLE_EXTERNAL_RESEARCH", "true")
    monkeypatch.setenv("GTM_DISABLE_LLM", "true")
    monkeypatch.delenv("REDIS_URL", raising=False)

    from gtm_agents.graph import run_pipeline

    out = run_pipeline(
        {
            "run_id": "00000000-0000-0000-0000-000000000000",
            "user_id": "00000000-0000-0000-0000-000000000001",
            "input": {"product_description": "A B2B SaaS that helps teams run multi-agent GTM research."},
        }
    )
    assert "final_markdown" in out
    assert "# GTM Strategy" in out["final_markdown"]
