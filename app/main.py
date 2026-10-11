"""mcp-service — shared tool/skill host with TWO faces:

1. Standard MCP endpoint at /mcp/{app}/ (Streamable HTTP, official SDK) — any MCP
   client connects and gets tools/list, tools/call, prompts/list, prompts/get,
   resources/list, resources/read.
2. Management REST API — CRUD for tools + skills, invoke, manifest, app keys, the
   invocation record, record history, and the Console at /admin.

See documents/console_specification.md for the model and the rules.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel

from app import activity, admin, auth, invoke, keys, oauth, registry, toolimpl, validation
from app.mcpserver import create_mcp_server
from app.mount import mount_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-service")

# Advertised over MCP `initialize` so any client can DISCOVER that this server
# also offers a registry-admin extension on the REST face.
_REGISTRY_CAPABILITY = {
    "registry": {
        "version": "2",
        "admin_transport": "rest",
        "operations": ["list", "get", "upsert", "delete", "history", "restore"],
        "resources": ["tools", "skills", "apps", "keys", "activity"],
        "endpoints": {
            "tools": "GET/PUT/DELETE /tools[/{name}]?app=",
            "skills": "GET/PUT/DELETE /skills[/{name}]?app=",
            "invoke": "POST /tools/{name}/invoke?app=",
            "manifest": "GET /tools/manifest?app=",
            "keys": "GET/POST /apps/{app}/keys, DELETE /apps/{app}/keys/{id}",
            "activity": "GET /activity, /activity/summary, /activity.csv",
            "history": "GET /tools/{name}/history, POST /tools/{name}/restore",
        },
        "auth": "app keys on invoke and MCP; admin bearer or the domain proxy's signed-in administrator on writes",
    }
}

registry.seed()
_mcp_server = create_mcp_server()
_orig_init_opts = _mcp_server.create_initialization_options


def _init_opts_with_registry(*args, **kwargs):
    kwargs.setdefault("experimental_capabilities", _REGISTRY_CAPABILITY)
    return _orig_init_opts(*args, **kwargs)


_mcp_server.create_initialization_options = _init_opts_with_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with _session_manager.run():
        yield


app = FastAPI(title="mcp-service", version="0.3.0", lifespan=lifespan)
_session_manager = mount_mcp(app, _mcp_server)
app.include_router(admin.router)


@app.exception_handler(auth.AuthError)
async def _auth_error(request: Request, e: auth.AuthError):
    headers = {"WWW-Authenticate": oauth.www_authenticate(None, e.detail)} if e.status == 401 else {}
    return JSONResponse({"error": {"code": "unauthorized" if e.status == 401 else "forbidden",
                                   "message": e.detail}}, status_code=e.status, headers=headers)


@app.exception_handler(oauth.OAuthError)
async def _oauth_error(request: Request, e: oauth.OAuthError):
    return JSONResponse(e.body(), status_code=e.status, headers={"Cache-Control": "no-store"})


def _actor(request: Request) -> str:
    """Who made a write, for the history: the console (admin token), the signed-in person,
    or a key id."""
    try:
        c = auth.resolve(request.headers)
    except auth.AuthError:
        return "unknown"
    return c.label if c.kind != "anonymous" else "open-dev"


# ── models ─────────────────────────────────────────────────────────────────
class ToolIn(BaseModel):
    display_name: str | None = None
    description: str | None = None
    impl: str | None = None
    tier: str | None = None
    destructive: bool | None = None
    idempotent: bool | None = None
    enabled: bool | None = None
    apps: list[str] | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None
    config: dict | None = None


class SkillIn(BaseModel):
    display_name: str | None = None
    description: str | None = None
    content: str | None = None
    arguments: list[dict] | None = None
    apps: list[str] | None = None
    tools: list[str] | None = None
    tags: list[str] | None = None
    enabled: bool | None = None


class EnabledIn(BaseModel):
    enabled: bool


class AppIn(BaseModel):
    display_name: str | None = None
    description: str | None = None
    owner: str | None = None
    contact: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class RestoreIn(BaseModel):
    version: int


class KeyIn(BaseModel):
    name: str = ""
    expires_days: int = 90


class RenderIn(BaseModel):
    arguments: dict = {}


class MachineClientIn(BaseModel):
    name: str = ""
    scopes: list[str] = ["tools:read"]


def _given(model: BaseModel) -> dict:
    return {k: v for k, v in model.model_dump().items() if v is not None}


# ── health ──────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return JSONResponse({
        "service": "mcp-service",
        "status": "ok",
        "version": app.version,
        "mcp_endpoint": "/mcp",
        "websearch_url": toolimpl.WEBSEARCH_URL,
        "tools": len(registry.list_tools()),
        "skills": len(registry.list_skills()),
        "apps": registry.apps(),
        "impls": sorted(toolimpl.IMPLS.keys()),
        "admin_auth": "bearer" if auth.admin_token() else "open",
        "proxy_identity": "configured" if auth.proxy_secret() else "off",
        "app_keys": auth.mode(),
        "oauth": {"issuer": oauth.public_url(), "clients": len(oauth.list_clients())},
        "record_args": activity.record_args(),
        "retention_days": activity.retention_days(),
        "experimental": _REGISTRY_CAPABILITY,
    })


@app.get("/backends/health")
async def backends_health():
    return JSONResponse({"backends": await admin.backends_status()})


# ── tools ───────────────────────────────────────────────────────────────────
@app.get("/tools")
async def tools_list(app: str | None = Query(None)):
    return JSONResponse({"tools": registry.list_tools(app)})


@app.get("/tools/manifest")
async def tools_manifest(app: str | None = Query(None)):
    """LLM-facing tool specs (enabled only) — what an orchestrator feeds a model."""
    specs = [{"name": t["name"], "description": t.get("description", ""),
              "input_schema": t.get("input_schema") or {"type": "object"}}
             for t in registry.list_tools(app) if t.get("enabled", True)]
    return JSONResponse({"tools": specs})


@app.get("/tools/{name}")
async def tool_get(name: str):
    t = registry.get_tool(name)
    if not t:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(t)


@app.put("/tools/{name}")
async def tool_put(name: str, body: ToolIn, request: Request, app: str | None = Query(None)):
    auth.require_admin(request.headers)
    data = _given(body)
    existing = registry.get_tool(name) or {}
    merged = {**existing, **data}
    if (merged.get("config") or {}).get("execution", "server") != "client" \
            and merged.get("impl") not in toolimpl.IMPLS:
        raise HTTPException(status_code=422,
                            detail=f"unknown impl '{merged.get('impl')}'; valid: {sorted(toolimpl.IMPLS)}")
    if "input_schema" in data:
        err = validation.schema_error(data["input_schema"])
        if err:
            raise HTTPException(status_code=422, detail=f"input_schema is not a valid JSON Schema: {err}")
    if not merged.get("apps") and not app:
        raise HTTPException(status_code=422, detail="a tool must be offered to at least one app (apps or ?app=)")
    unknown = registry.unknown_apps((data.get("apps") or []) + ([app] if app else []))
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown app(s): {', '.join(unknown)}; register them first (Apps › New app)")
    try:
        return JSONResponse(registry.put_tool(name, data, actor=_actor(request), app=app))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.patch("/tools/{name}/enabled")
async def tool_set_enabled(name: str, body: EnabledIn, request: Request):
    auth.require_admin(request.headers)
    if not registry.get_tool(name):
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(registry.put_tool(name, {"enabled": body.enabled}, actor=_actor(request)))


@app.delete("/tools/{name}")
async def tool_delete(name: str, request: Request, app: str | None = Query(None)):
    auth.require_admin(request.headers)
    return JSONResponse({"deleted": registry.delete_tool(name, actor=_actor(request), app=app)})


@app.get("/tools/{name}/history")
async def tool_history(name: str):
    return JSONResponse({"history": registry.history("tool", name)})


@app.post("/tools/{name}/restore")
async def tool_restore(name: str, body: RestoreIn, request: Request):
    auth.require_admin(request.headers)
    try:
        return JSONResponse(registry.restore("tool", name, body.version, actor=_actor(request)))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


def _app_for(tool: dict, app: str | None) -> str | None:
    """The app a call is for: the ``?app=`` given (must be one the tool is offered to), or
    the tool's only app, or None for a tool offered to several apps and no choice made."""
    apps = tool.get("apps") or []
    chosen = app if app else (apps[0] if len(apps) == 1 else None)
    if app and app not in apps:
        raise HTTPException(status_code=404, detail=f"tool '{tool['name']}' is not offered to app '{app}'")
    if chosen and (registry.get_app(chosen) or {}).get("status") == "retired":
        raise HTTPException(status_code=403, detail=f"app '{chosen}' is retired")
    return chosen


@app.post("/tools/{name}/invoke")
async def tool_invoke(name: str, request: Request, app: str | None = Query(None)):
    t = registry.get_tool(name)
    if not t:
        return JSONResponse({"error": "not found"}, status_code=404)
    scope = _app_for(t, app)
    caller = auth.resolve(request.headers)
    if caller.kind == "anonymous" and auth.is_public(request.headers):
        raise auth.AuthError(401, "sign in with OAuth, or present an app key (Authorization: Bearer …)")
    obo = request.headers.get("x-on-behalf-of") or caller.email
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    args = body.get("args", body) if isinstance(body, dict) else {}
    try:
        result = await invoke.run(t, scope, args, caller, obo, "rest")
    except invoke.InvokeError as e:
        return JSONResponse({"error": e.error}, status_code=e.status)
    return JSONResponse({"tool": name, "app": scope, "result": result})


# ── skills ──────────────────────────────────────────────────────────────────
@app.get("/skills")
async def skills_list(app: str | None = Query(None)):
    return JSONResponse({"skills": registry.list_skills(app)})


@app.get("/skills/{name}")
async def skill_get(name: str):
    s = registry.get_skill(name)
    if not s:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(s)


@app.put("/skills/{name}")
async def skill_put(name: str, body: SkillIn, request: Request, app: str | None = Query(None)):
    auth.require_admin(request.headers)
    data = _given(body)
    for a in data.get("arguments") or []:
        if not isinstance(a, dict) or not a.get("name"):
            raise HTTPException(status_code=422, detail="each argument needs a name")
    existing = registry.get_skill(name) or {}
    if not ({**existing, **data}.get("apps")) and not app:
        raise HTTPException(status_code=422, detail="a skill must be offered to at least one app (apps or ?app=)")
    unknown = registry.unknown_apps((data.get("apps") or []) + ([app] if app else []))
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown app(s): {', '.join(unknown)}; register them first (Apps › New app)")
    try:
        return JSONResponse(registry.put_skill(name, data, actor=_actor(request), app=app))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.patch("/skills/{name}/enabled")
async def skill_set_enabled(name: str, body: EnabledIn, request: Request):
    auth.require_admin(request.headers)
    if not registry.get_skill(name):
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(registry.put_skill(name, {"enabled": body.enabled}, actor=_actor(request)))


@app.delete("/skills/{name}")
async def skill_delete(name: str, request: Request, app: str | None = Query(None)):
    auth.require_admin(request.headers)
    return JSONResponse({"deleted": registry.delete_skill(name, actor=_actor(request), app=app)})


@app.get("/skills/{name}/history")
async def skill_history(name: str):
    return JSONResponse({"history": registry.history("skill", name)})


@app.post("/skills/{name}/restore")
async def skill_restore(name: str, body: RestoreIn, request: Request):
    auth.require_admin(request.headers)
    try:
        return JSONResponse(registry.restore("skill", name, body.version, actor=_actor(request)))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/skills/{name}/render")
async def skill_render(name: str, body: RenderIn):
    """Exactly what ``prompts/get`` returns for these arguments (the console's Try it)."""
    s = registry.get_skill(name)
    if not s:
        return JSONResponse({"error": "not found"}, status_code=404)
    missing = [a["name"] for a in s.get("arguments", []) if a.get("required") and not body.arguments.get(a["name"])]
    if missing:
        return JSONResponse({"error": {"code": "missing_arguments", "message": f"missing: {', '.join(missing)}"}},
                            status_code=422)
    return JSONResponse({"name": name, "description": s.get("description", ""),
                         "messages": [{"role": "user", "content": registry.render_skill(s, body.arguments)}]})


# ── apps and keys ───────────────────────────────────────────────────────────
def _app_view(name: str, rec: dict | None, tools, skills, all_keys) -> dict:
    ks = [k for k in all_keys if k["app"] == name and not k.get("revoked_at")]
    return {**registry.APP_DEFAULTS, **(rec or {}), "name": name, "registered": rec is not None,
            "endpoint": f"/mcp/{name}/", "rest": f"/tools?app={name}",
            "tools": sum(1 for t in tools if name in t.get("apps", [])),
            "skills": sum(1 for s in skills if name in s.get("apps", [])),
            "keys": ks, "clients": oauth.list_clients(app=name, kind="machine")}


@app.get("/apps")
async def apps_list():
    """The application catalog: every registered app with what it is offered and its keys; an app a record
    still names without a registration appears too, flagged ``registered: false``."""
    tools, skills, all_keys = registry.list_tools(), registry.list_skills(), keys.list_keys()
    records = {a["name"]: a for a in registry.list_apps()}
    return JSONResponse({"apps": [_app_view(n, records.get(n), tools, skills, all_keys) for n in registry.apps()]})


@app.get("/apps/{name}")
async def app_get(name: str):
    rec = registry.get_app(name)
    if not rec and name not in registry.apps():
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(_app_view(name, rec, registry.list_tools(), registry.list_skills(), keys.list_keys()))


@app.put("/apps/{name}")
async def app_put(name: str, body: AppIn, request: Request):
    auth.require_admin(request.headers)
    try:
        return JSONResponse(registry.put_app(name, _given(body), actor=_actor(request)))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.delete("/apps/{name}")
async def app_delete(name: str, request: Request, force: bool = Query(False)):
    auth.require_admin(request.headers)
    active = [k for k in keys.list_keys(name) if not k.get("revoked_at")]
    if active and not force:
        raise HTTPException(status_code=409, detail=f"{name} has {len(active)} active key(s); revoke them first, or delete with force")
    try:
        deleted = registry.delete_app(name, actor=_actor(request), force=force)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    if deleted and force:
        for k in active:
            keys.revoke(k["id"])
        for c in oauth.list_clients(app=name, kind="machine"):
            oauth.delete_client(c["client_id"])
    return JSONResponse({"deleted": deleted})


@app.get("/apps/{name}/history")
async def app_history(name: str):
    return JSONResponse({"history": registry.history("app", name)})


@app.post("/apps/{name}/restore")
async def app_restore(name: str, body: RestoreIn, request: Request):
    auth.require_admin(request.headers)
    try:
        return JSONResponse(registry.restore("app", name, body.version, actor=_actor(request)))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/apps/{app}/keys")
async def keys_list(app: str):
    return JSONResponse({"keys": keys.list_keys(app)})


@app.post("/apps/{app}/keys")
async def keys_create(app: str, body: KeyIn, request: Request):
    auth.require_admin(request.headers)
    try:
        plaintext, rec = keys.create(app, body.name, body.expires_days)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return JSONResponse({"key": plaintext, "record": rec}, status_code=201)


@app.get("/apps/{app}/clients")
async def machine_clients(app: str):
    return JSONResponse({"clients": oauth.list_clients(app=app, kind="machine")})


@app.post("/apps/{app}/clients")
async def machine_client_create(app: str, body: MachineClientIn, request: Request):
    """A machine client for the client credentials grant: bound to the app, the secret shown once."""
    auth.require_admin(request.headers)
    return JSONResponse(oauth.register_machine_client(app, body.name, body.scopes), status_code=201,
                        headers={"Cache-Control": "no-store"})


@app.delete("/apps/{app}/clients/{client_id}")
async def machine_client_delete(app: str, client_id: str, request: Request):
    auth.require_admin(request.headers)
    rec = next((c for c in oauth.list_clients(app=app, kind="machine") if c["client_id"] == client_id), None)
    if not rec:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({"deleted": oauth.delete_client(client_id)})


@app.delete("/apps/{app}/keys/{key_id}")
async def keys_revoke(app: str, key_id: str, request: Request):
    auth.require_admin(request.headers)
    rec = next((k for k in keys.list_keys(app) if k["id"] == key_id), None)
    if not rec:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({"revoked": keys.revoke(key_id)})


# ── OAuth 2.1 (app/oauth.py): the authorization server and the resource metadata ────────────────
@app.get("/.well-known/oauth-authorization-server")
async def oauth_as_metadata():
    return JSONResponse(oauth.authorization_server_metadata(), headers={"Cache-Control": "public, max-age=300"})


@app.get("/.well-known/oauth-protected-resource")
async def oauth_resource_metadata():
    return JSONResponse(oauth.protected_resource_metadata(), headers={"Cache-Control": "public, max-age=300"})


@app.get("/.well-known/oauth-protected-resource/{path:path}")
async def oauth_resource_metadata_path(path: str):
    """RFC 9728 path-aware form: the metadata of one app's endpoint, ``…/oauth-protected-resource/mcp/{app}/``."""
    segs = [p for p in path.split("/") if p]
    app_name = segs[1] if len(segs) >= 2 and segs[0] == "mcp" else None
    return JSONResponse(oauth.protected_resource_metadata(app_name), headers={"Cache-Control": "public, max-age=300"})


@app.post("/oauth/register", status_code=201)
async def oauth_register(request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        raise oauth.OAuthError("invalid_client_metadata", "the body must be JSON")
    return JSONResponse(oauth.register_client(body if isinstance(body, dict) else {}), status_code=201,
                        headers={"Cache-Control": "no-store"})


@app.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    """The consent page, for the person the domain proxy signed in (the route is behind its Entra gate)."""
    user = auth.person_from(request.headers)
    if not user:
        return HTMLResponse("<h1>Sign in first</h1><p>This address is reachable only through the domain, where "
                            "Microsoft Entra ID signs you in before this page.</p>", status_code=401)
    pending = oauth.begin_authorization(dict(request.query_params), user)
    base = request.headers.get("x-forwarded-prefix") or ""
    return HTMLResponse(oauth.consent_page(pending, base), headers={"Cache-Control": "no-store"})


@app.post("/oauth/decision")
async def oauth_decision(request: Request):
    user = auth.person_from(request.headers)
    if not user:
        raise auth.AuthError(401, "sign in through the domain first")
    form = await request.form()
    location = oauth.decide(str(form.get("rid") or ""), form.get("decision") == "allow", user)
    return RedirectResponse(location, status_code=302, headers={"Cache-Control": "no-store"})


@app.post("/oauth/token")
async def oauth_token(request: Request):
    form = {k: str(v) for k, v in (await request.form()).items()}
    return JSONResponse(oauth.token(form), headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


@app.post("/oauth/revoke")
async def oauth_revoke(request: Request):
    form = {k: str(v) for k, v in (await request.form()).items()}
    oauth.revoke(form)
    return JSONResponse({}, headers={"Cache-Control": "no-store"})


@app.get("/oauth/clients")
async def oauth_clients():
    return JSONResponse({"clients": oauth.list_clients()})


@app.delete("/oauth/clients/{client_id}")
async def oauth_client_delete(client_id: str, request: Request):
    auth.require_admin(request.headers)
    return JSONResponse({"deleted": oauth.delete_client(client_id)})


# ── activity ────────────────────────────────────────────────────────────────
@app.get("/activity")
async def activity_list(app: str | None = None, tool: str | None = None, caller: str | None = None,
                        on_behalf_of: str | None = None, transport: str | None = None,
                        ok: bool | None = None, window: str | None = "24h", since: str | None = None,
                        until: str | None = None, q: str | None = None, limit: int = 100,
                        cursor: str | None = None):
    return JSONResponse(activity.query(limit=limit, cursor=cursor, window=window, since=since, until=until,
                                       app=app, tool=tool, caller=caller, on_behalf_of=on_behalf_of,
                                       transport=transport, ok=ok, q=q))


@app.get("/activity/summary")
async def activity_summary(window: str = "24h", app: str | None = None):
    if window not in activity.WINDOWS:
        raise HTTPException(status_code=422, detail=f"window must be one of {sorted(activity.WINDOWS)}")
    return JSONResponse(activity.summary(window, app))


@app.get("/activity.csv")
async def activity_csv(app: str | None = None, tool: str | None = None, caller: str | None = None,
                       ok: bool | None = None, window: str | None = "24h", since: str | None = None,
                       until: str | None = None, q: str | None = None):
    text = activity.to_csv(window=window, since=since, until=until, app=app, tool=tool, caller=caller, ok=ok, q=q)
    return PlainTextResponse(text, media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="activity.csv"'})
