from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_research_server_path() -> Path:
    configured = os.getenv("GTM_RESEARCH_MCP_SERVER")
    if configured:
        return Path(configured)
    return _repo_root() / "services" / "mcp" / "research_server.py"


def _server_env() -> dict[str, str]:
    env = dict(os.environ)
    src = str(_repo_root() / "services" / "agents" / "src")
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src}{os.pathsep}{current}" if current else src
    return env


def _content_to_json(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured

    content = getattr(result, "content", None) or []
    texts: list[str] = []
    for part in content:
        text = getattr(part, "text", None)
        if text:
            texts.append(str(text))
    raw = "\n".join(texts).strip()
    if not raw:
        return {"items": [], "warnings": ["MCP tool returned no content."]}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"items": parsed, "warnings": []}
    except json.JSONDecodeError:
        return {"items": [], "warnings": [raw]}


async def _list_tools_async() -> list[dict[str, Any]]:
    server = StdioServerParameters(command=sys.executable, args=[str(default_research_server_path())], env=_server_env())
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = []
            for tool in response.tools:
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                )
            return tools


async def _call_tools_async(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    server = StdioServerParameters(command=sys.executable, args=[str(default_research_server_path())], env=_server_env())
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            results: list[dict[str, Any]] = []
            for call in calls:
                name = str(call.get("tool_name") or call.get("name") or "")
                arguments = call.get("arguments") or {}
                if not name:
                    results.append({"items": [], "warnings": ["Skipped MCP call without tool_name."], "tool_name": name})
                    continue
                try:
                    raw = await session.call_tool(name, arguments)
                    parsed = _content_to_json(raw)
                    parsed["tool_name"] = name
                    parsed["arguments"] = arguments
                    parsed["reason"] = call.get("reason")
                    results.append(parsed)
                except Exception as e:
                    results.append(
                        {
                            "items": [],
                            "warnings": [f"MCP tool {name} failed: {e}"],
                            "tool_name": name,
                            "arguments": arguments,
                            "reason": call.get("reason"),
                        }
                    )
            return results


def list_research_tools() -> list[dict[str, Any]]:
    return asyncio.run(_list_tools_async())


def call_research_tools(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return asyncio.run(_call_tools_async(calls))
