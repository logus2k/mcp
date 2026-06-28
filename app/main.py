"""mcp-service — shared tool/skill host with TWO faces:

1. Standard MCP endpoint at /mcp/ (Streamable HTTP, official SDK) — any MCP
   client connects and gets tools/list, tools/call, prompts/list, prompts/get.
2. Management REST API — CRUD for tools + skills (the job2cool admin UI), plus
   /tools/{name}/invoke and /tools/manifest. (MCP is for consumption, not
   authoring, so authoring lives on this separate REST face.)

Networks: noted-network (apps reach this service) + mcp_internal (this service
reaches the isolated websearch_server). web_search delegates there.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import admin, registry, toolimpl
from app.mcpserver import create_mcp_server
from app.mount import mount_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-service")

# Admin (write) auth. When set, PUT/DELETE require `Authorization: Bearer <token>`.
# Reads + tool consumption stay open (internal network). Empty = open (dev).
ADMIN_TOKEN = os.getenv("MCP_ADMIN_TOKEN", "")

# Advertised over MCP `initialize` so any client can DISCOVER that this server
# also offers a registry-admin extension. The admin operations themselves bind
# to the REST face below (the SDK validates JSON-RPC against known methods, so a
# custom JSON-RPC method set isn't portable; REST is universal + browser-safe).
_REGISTRY_CAPABILITY = {
    "registry": {
        "version": "1",
        "admin_transport": "rest",
        "operations": ["list", "get", "upsert", "delete"],
        "resources": ["tools", "skills"],
        "endpoints": {
            "tools": "GET/PUT/DELETE /tools[/{name}]?app=",
            "skills": "GET/PUT/DELETE /skills[/{name}]?app=",
            "invoke": "POST /tools/{name}/invoke?app=",
            "manifest": "GET /tools/manifest?app=",
        },
        "auth": "bearer (writes)" if ADMIN_TOKEN else "open",
    }
}


def _require_admin(authorization: str | None) -> None:
    if not ADMIN_TOKEN:
        return
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="admin bearer token required")


registry.seed()
_mcp_server = create_mcp_server()

# Inject the experimental capability into the init options the session manager
# builds (it calls server.create_initialization_options() with no args).
_orig_init_opts = _mcp_server.create_initialization_options


def _init_opts_with_registry(*args, **kwargs):
    kwargs.setdefault("experimental_capabilities", _REGISTRY_CAPABILITY)
    return _orig_init_opts(*args, **kwargs)


_mcp_server.create_initialization_options = _init_opts_with_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with _session_manager.run():
        yield


app = FastAPI(title="mcp-service", version="0.1.0", lifespan=lifespan)
_session_manager = mount_mcp(app, _mcp_server)
app.include_router(admin.router)  # read-only browser view at /admin


# ── models ─────────────────────────────────────────────────────────────────
class ToolIn(BaseModel):
    display_name: str = ""
    description: str = ""
    impl: str = "web_search"
    tier: str = "read"
    enabled: bool = True
    input_schema: dict = {}
    config: dict = {}


class SkillIn(BaseModel):
    display_name: str = ""
    description: str = ""
    content: str = ""
    triggers: list[str] = []
    priority: int = 100
    enabled: bool = True


class EnabledIn(BaseModel):
    enabled: bool


# ── health ──────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return JSONResponse({
        "service": "mcp-service",
        "status": "ok",
        "mcp_endpoint": "/mcp",
        "websearch_url": toolimpl.WEBSEARCH_URL,
        "tools": len(registry.list_tools()),
        "skills": len(registry.list_skills()),
        "impls": sorted(toolimpl.IMPLS.keys()),
        "admin_auth": "bearer" if ADMIN_TOKEN else "open",
        "experimental": _REGISTRY_CAPABILITY,
    })


@app.get("/backends/health")
async def backends_health():
    """Liveness of the tool backends mcp-service fronts. websearch_server lives on
    mcp_internal and is unreachable from other networks (e.g. job2cool-backend),
    so this endpoint lets them observe it THROUGH mcp-service. Side-effect-free —
    pings the backend's /health only (no real web search). Reads stay open.
    The probe lives in app.admin so the /admin/health view reuses it."""
    return JSONResponse({"backends": await admin.backends_status()})


# ── tools (management REST) ──────────────────────────────────────────────────
@app.get("/tools")
async def tools_list(app: str = Query("job2cool")):
    return JSONResponse({"tools": registry.list_tools(app)})


@app.get("/tools/manifest")
async def tools_manifest(app: str = Query("job2cool")):
    """LLM-facing tool specs (enabled only) — what an orchestrator feeds a model."""
    specs = [{"name": t["name"], "description": t.get("description", ""),
              "input_schema": t.get("input_schema") or {"type": "object"}}
             for t in registry.list_tools(app) if t.get("enabled", True)]
    return JSONResponse({"tools": specs})


@app.get("/tools/{name}")
async def tool_get(name: str, app: str = Query("job2cool")):
    t = registry.get_tool(app, name)
    if not t:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(t)


@app.put("/tools/{name}")
async def tool_put(name: str, body: ToolIn, app: str = Query("job2cool"),
                   authorization: str | None = Header(None)):
    _require_admin(authorization)
    data = body.model_dump()
    # Server-executed tools must bind to a shipped impl; client-executed tools
    # (config.execution == "client", e.g. tutor UI actions) carry a client-side
    # impl id that this service never runs, so skip the check for them.
    if (data.get("config") or {}).get("execution", "server") != "client" \
            and data["impl"] not in toolimpl.IMPLS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown impl '{data['impl']}'; valid: {sorted(toolimpl.IMPLS)}",
        )
    return JSONResponse(registry.put_tool(app, name, data))


@app.patch("/tools/{name}/enabled")
async def tool_set_enabled(name: str, body: EnabledIn, app: str = Query("job2cool"),
                           authorization: str | None = Header(None)):
    _require_admin(authorization)
    if not registry.get_tool(app, name):
        return JSONResponse({"error": "not found"}, status_code=404)
    # Partial update — put_tool merges over the existing record, preserving impl,
    # schema, config, timestamps; only `enabled` changes.
    return JSONResponse(registry.put_tool(app, name, {"enabled": body.enabled}))


@app.delete("/tools/{name}")
async def tool_delete(name: str, app: str = Query("job2cool"),
                      authorization: str | None = Header(None)):
    _require_admin(authorization)
    return JSONResponse({"deleted": registry.delete_tool(app, name)})


@app.post("/tools/{name}/invoke")
async def tool_invoke(name: str, request: Request, app: str = Query("job2cool")):
    t = registry.get_tool(app, name)
    if not t:
        return JSONResponse({"error": "not found"}, status_code=404)
    if not t.get("enabled", True):
        return JSONResponse({"error": "tool disabled"}, status_code=409)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    args = body.get("args", body) if isinstance(body, dict) else {}
    try:
        result = await toolimpl.invoke(t["impl"], args, t.get("config") or {})
    except Exception as e:  # noqa: BLE001
        logger.exception("invoke failed")
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)
    return JSONResponse({"tool": name, "result": result})


# ── skills (management REST) ─────────────────────────────────────────────────
@app.get("/skills")
async def skills_list(app: str = Query("job2cool")):
    return JSONResponse({"skills": registry.list_skills(app)})


@app.get("/skills/{name}")
async def skill_get(name: str, app: str = Query("job2cool")):
    s = registry.get_skill(app, name)
    if not s:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(s)


@app.put("/skills/{name}")
async def skill_put(name: str, body: SkillIn, app: str = Query("job2cool"),
                    authorization: str | None = Header(None)):
    _require_admin(authorization)
    return JSONResponse(registry.put_skill(app, name, body.model_dump()))


@app.patch("/skills/{name}/enabled")
async def skill_set_enabled(name: str, body: EnabledIn, app: str = Query("job2cool"),
                            authorization: str | None = Header(None)):
    _require_admin(authorization)
    if not registry.get_skill(app, name):
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(registry.put_skill(app, name, {"enabled": body.enabled}))


@app.delete("/skills/{name}")
async def skill_delete(name: str, app: str = Query("job2cool"),
                       authorization: str | None = Header(None)):
    _require_admin(authorization)
    return JSONResponse({"deleted": registry.delete_skill(app, name)})
