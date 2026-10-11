"""The standard MCP server surface (official ``mcp`` SDK).

Exposes the registry over the Model Context Protocol so ANY MCP client can use it:
tools → MCP tools (with annotations and output schemas), skills → MCP prompts (with
arguments) and ``skill://`` resources. The app, the caller and the on-behalf-of address
are set per request by ``mount.py`` in context variables.
"""
from __future__ import annotations

import contextvars
import json

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents

from app import auth, invoke, registry

# None = no app scope → everything enabled (the aggregate view).
current_app: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_app", default=None)
current_caller: contextvars.ContextVar[auth.Caller] = contextvars.ContextVar("current_caller", default=auth.ANONYMOUS)
current_obo: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_obo", default=None)

SKILL_SCHEME = "skill://"


def tool_annotations(t: dict) -> types.ToolAnnotations:
    read_only = t.get("tier", "read") == "read"
    return types.ToolAnnotations(
        title=t.get("display_name") or None,
        readOnlyHint=read_only,
        destructiveHint=False if read_only else bool(t.get("destructive", False)),
        idempotentHint=True if read_only else bool(t.get("idempotent", False)),
    )


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
                title=t.get("display_name") or None,
                description=t.get("description", ""),
                inputSchema=t.get("input_schema") or {"type": "object"},
                outputSchema=t.get("output_schema") or None,
                annotations=tool_annotations(t),
            ))
        return out

    # Validation happens in app.invoke (recorded, same error shape on both faces).
    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict | None):
        app = current_app.get()
        matches = [t for t in registry.list_tools(app) if t["name"] == name and t.get("enabled", True)]
        if not matches:
            raise ValueError(f"unknown or disabled tool: {name}")
        t = matches[0]
        try:
            result = await invoke.run(t, app, arguments or {}, current_caller.get(), current_obo.get(), "mcp")
        except invoke.InvokeError as e:
            raise ValueError(f"{e.error.get('code')}: {e.error.get('message')}"
                             + (f" (at {e.error['path']})" if e.error.get("path") else "")) from e
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        content = [types.TextContent(type="text", text=text)]
        if t.get("output_schema") and isinstance(result, dict):
            return content, result
        return content

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        out = []
        for s in registry.list_skills(current_app.get()):
            if not s.get("enabled", True):
                continue
            out.append(types.Prompt(
                name=s["name"],
                title=s.get("display_name") or None,
                description=s.get("description", ""),
                arguments=[types.PromptArgument(name=a["name"], description=a.get("description", ""),
                                                required=bool(a.get("required", False)))
                           for a in s.get("arguments", [])],
            ))
        return out

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
        matches = [s for s in registry.list_skills(current_app.get())
                   if s["name"] == name and s.get("enabled", True)]
        if not matches:
            raise ValueError(f"unknown or disabled prompt: {name}")
        s = matches[0]
        missing = [a["name"] for a in s.get("arguments", []) if a.get("required") and not (arguments or {}).get(a["name"])]
        if missing:
            raise ValueError(f"missing required argument(s): {', '.join(missing)}")
        return types.GetPromptResult(
            description=s.get("description", ""),
            messages=[types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=registry.render_skill(s, arguments)),
            )],
        )

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [types.Resource(uri=f"{SKILL_SCHEME}{s['name']}", name=s["name"],
                               title=s.get("display_name") or None,
                               description=s.get("description", ""), mimeType="text/markdown")
                for s in registry.list_skills(current_app.get()) if s.get("enabled", True)]

    @server.read_resource()
    async def read_resource(uri):
        text = str(uri)
        if not text.startswith(SKILL_SCHEME):
            raise ValueError(f"unknown resource: {text}")
        name = text[len(SKILL_SCHEME):].strip("/")
        matches = [s for s in registry.list_skills(current_app.get())
                   if s["name"] == name and s.get("enabled", True)]
        if not matches:
            raise ValueError(f"unknown or disabled skill: {name}")
        return [ReadResourceContents(content=matches[0].get("content", ""), mime_type="text/markdown")]

    return server
