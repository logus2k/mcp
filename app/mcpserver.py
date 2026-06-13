"""The standard MCP server surface (official `mcp` SDK).

Exposes the registry over the Model Context Protocol so ANY MCP client can use
it: tools → MCP tools (tools/list, tools/call); skills → MCP prompts
(prompts/list, prompts/get). Trigger-based auto-injection is a consumer concern;
MCP just serves the catalog + content.
"""
from __future__ import annotations

import contextvars
import json

import mcp.types as types
from mcp.server.lowlevel import Server

from app import registry, toolimpl

# Set per-request from the /mcp/{app}/ path segment (see mount.py). None = no
# app scope → expose everything enabled (aggregate/admin view).
current_app: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_app", default=None)


def create_mcp_server() -> Server:
    server = Server("mcp-service")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        out = []
        for t in registry.list_tools(current_app.get()):
            if not t.get("enabled", True):
                continue
            out.append(types.Tool(
                name=t["name"],
                description=t.get("description", ""),
                inputSchema=t.get("input_schema") or {"type": "object"},
            ))
        return out

    @server.call_tool()
    async def call_tool(name: str, arguments: dict | None):
        matches = [t for t in registry.list_tools(current_app.get())
                   if t["name"] == name and t.get("enabled", True)]
        if not matches:
            raise ValueError(f"unknown or disabled tool: {name}")
        t = matches[0]
        result = await toolimpl.invoke(t["impl"], arguments or {}, t.get("config") or {})
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        return [types.TextContent(type="text", text=text)]

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        out = []
        for s in registry.list_skills(current_app.get()):
            if not s.get("enabled", True):
                continue
            out.append(types.Prompt(name=s["name"], description=s.get("description", "")))
        return out

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
        matches = [s for s in registry.list_skills(current_app.get())
                   if s["name"] == name and s.get("enabled", True)]
        if not matches:
            raise ValueError(f"unknown or disabled prompt: {name}")
        s = matches[0]
        return types.GetPromptResult(
            description=s.get("description", ""),
            messages=[types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=s.get("content", "")),
            )],
        )

    return server
