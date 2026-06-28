from stoa_core.agent.progress import AgentProgressCallback, format_tool_label


def test_format_tool_label_known_tool() -> None:
    assert format_tool_label("search_workspace_memory") == "workspace memory"


def test_format_tool_label_unknown_tool() -> None:
    assert format_tool_label("custom_tool_name") == "custom tool name"


def test_agent_progress_callback_emits_tool_events() -> None:
    events: list[dict] = []
    handler = AgentProgressCallback(events.append)

    handler.on_tool_start({"name": "search_workspace_memory"}, "query", run_id="1")  # type: ignore[arg-type]
    handler.on_tool_end("ok", run_id="1")  # type: ignore[arg-type]

    assert [event["status"] for event in events] == [
        "tool_call",
        "tool_done",
        "tool_summary",
    ]
    assert events[0]["message"] == "Calling workspace memory…"
    assert events[-1]["used_tools"] == ["search_workspace_memory"]
