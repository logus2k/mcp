"""The Console's data endpoints and page (console_specification.md section 5).

Reads are open on the internal network, like the rest of the REST read surface. The
page's writes call the bearer-gated endpoints in main.py with the admin token the
operator pastes into the page (kept in session storage, never in the page source).

    GET /admin            the Console (one self-contained HTML page)
    GET /admin/registry   tools, skills, apps, impls and coverage analysis in one read
    GET /admin/health     service, backends, auth mode (polled by the header)
    GET /admin/attention  what needs a decision (the Overview's list)
    GET /admin/export     downloadable registry JSON (full or ?app= slice)
"""
from __future__ import annotations

import os

import httpx
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from app import activity, auth, identity, keys, registry, toolimpl
from app.console_page import PAGE

router = APIRouter()


# ── backend liveness (shared with main.backends_health) ─────────────────────
async def probe_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.get(url)
        return "degraded" if r.status_code >= 500 else "ok"
    except Exception:  # noqa: BLE001 — any connect/timeout means unreachable
        return "down"


async def backends_status() -> dict:
    out = {"websearch_server": await probe_url(f"{toolimpl.WEBSEARCH_URL}/health")}
    jenkins = os.getenv("JENKINS_URL", "")
    if jenkins:
        out["jenkins"] = await probe_url(f"{jenkins.rstrip('/')}/login")
    out["newsapi"] = "configured" if os.getenv("NEWSAPI_KEY") else "not configured"
    out["proxy_conf"] = "mounted" if os.path.isdir(os.getenv("PROXY_CONF_DIR", "/proxy-conf")) else "missing"
    return out


# ── analysis helpers ────────────────────────────────────────────────────────
def execution(tool: dict) -> str:
    return (tool.get("config") or {}).get("execution", "server")


def is_orphan(tool: dict) -> bool:
    """Server-executed tool bound to an impl that doesn't exist. Client-executed tools
    carry a client-side impl id this service never runs — never orphans."""
    return execution(tool) != "client" and tool.get("impl") not in toolimpl.IMPLS


# ── data endpoints ──────────────────────────────────────────────────────────
@router.get("/admin/registry")
async def admin_registry():
    tools = registry.list_tools()
    skills = registry.list_skills()
    apps = registry.apps()
    impls = sorted(toolimpl.IMPLS.keys())
    referenced = {t.get("impl") for t in tools if execution(t) != "client"}
    summary = activity.summary("24h")
    by_tool = {t["tool"]: t for t in summary["tools"]}
    for t in tools:
        t["last_used"] = summary["last_used"].get(t["name"])
        t["calls_24h"] = by_tool.get(t["name"], {}).get("calls", 0)
        t["errors_24h"] = by_tool.get(t["name"], {}).get("errors", 0)
    return JSONResponse({
        "apps": apps,
        "tools": tools,
        "skills": skills,
        "impls": impls,
        "impl_tools": {i: [t["name"] for t in tools if t.get("impl") == i] for i in impls},
        "orphans": [t["name"] for t in tools if is_orphan(t)],
        "unused_impls": [i for i in impls if i not in referenced],
        "keys": keys.list_keys(),
        "app_records": registry.list_apps(),
        "summary": {k: v for k, v in summary.items() if k != "last_used"},
        "counts": {
            "apps": len(apps),
            "tools": len(tools),
            "tools_enabled": sum(1 for t in tools if t.get("enabled", True)),
            "skills": len(skills),
            "skills_enabled": sum(1 for s in skills if s.get("enabled", True)),
        },
    })


@router.get("/admin/me")
async def admin_me(request: Request):
    """Who the page is running as: the domain proxy's signed-in person (Microsoft Entra ID),
    the admin token, or nobody. The proxy's sign-out lives at the domain root."""
    try:
        c = auth.resolve(request.headers)
    except auth.AuthError:
        c = auth.ANONYMOUS
    out = {"email": c.email, "kind": c.kind, "label": c.label, "via": c.via, "admin": c.kind == "admin",
           "name": None, "picture": None, "sign_out": None}
    if c.via == "proxy" and c.email:
        info = await identity.profile(request.headers.get("x-access-token"))
        out["name"] = info.get("name") or c.email.split("@")[0]
        out["picture"] = info.get("picture")
        out["sign_out"] = identity.sign_out_url(request.headers.get("x-id-token"))
    return JSONResponse(out)


@router.get("/admin/health")
async def admin_health():
    return JSONResponse({
        "service": "ok",
        "admin_auth": "bearer" if auth.admin_token() else "open",
        "proxy_identity": "configured" if auth.proxy_secret() else "off",
        "app_keys": auth.mode(),
        "record_args": activity.record_args(),
        "retention_days": activity.retention_days(),
        "impls": len(toolimpl.IMPLS),
        "backends": await backends_status(),
    })


@router.get("/admin/attention")
async def admin_attention():
    """What needs a decision, each with why and where to go."""
    tools, skills = registry.list_tools(), registry.list_skills()
    items = []
    last_used = activity.summary("30d")["last_used"]
    never = [t["name"] for t in tools if execution(t) == "server" and t.get("enabled", True)
             and t["name"] not in last_used]
    if never:
        items.append({"level": "warn", "title": f"{len(never)} server tools were never called in the retained window",
                      "why": "Enabled, executed here, and no call recorded. Either nobody needs them or nobody "
                             "has connected yet.", "go": "#tools", "names": never})
    if not auth.require_keys():
        items.append({"level": "bad", "title": "App keys are optional: read-tier tools answer anonymous calls",
                      "why": "MCP_REQUIRE_KEYS is not 1. Write-tier tools already refuse anonymous calls; "
                             "set the flag once every consumer has a key.", "go": "#settings"})
    anon = activity.query(limit=1, window="24h", caller="anonymous")["calls"]
    if anon:
        items.append({"level": "warn", "title": "Anonymous calls in the last 24 h",
                      "why": f"Latest: {anon[0]['tool']} for app {anon[0]['app'] or '?'}. Give that consumer a key.",
                      "go": "#activity"})
    orphans = [t["name"] for t in tools if is_orphan(t)]
    if orphans:
        items.append({"level": "bad", "title": f"{len(orphans)} tool(s) bind to an implementation that does not exist",
                      "why": ", ".join(orphans), "go": "#settings", "names": orphans})
    for s in skills:
        offered = {t["name"] for t in tools if set(t.get("apps", [])) & set(s.get("apps", []))}
        missing = [x for x in s.get("tools", []) if x not in offered]
        if missing and s.get("tools"):
            items.append({"level": "info", "title": f"Skill {s['name']} expects tools its apps are not offered here",
                          "why": f"{', '.join(missing)}: either they are the app's own tools (fine) or they should be "
                                 "offered here.", "go": "#skills", "names": [s["name"]]})
    registered = {a["name"]: a for a in registry.list_apps()}
    unregistered = [a for a in registry.apps() if a not in registered]
    if unregistered:
        items.append({"level": "warn", "title": f"{len(unregistered)} app(s) named by records are not registered: {', '.join(unregistered)}",
                      "why": "A tool or skill offers itself to a name the catalog does not know. Register it, or withdraw the offer.",
                      "go": "#apps", "names": unregistered})
    retired_keys = [a for a, r in registered.items() if r.get("status") == "retired" and any(k["app"] == a and not k.get("revoked_at") for k in keys.list_keys())]
    if retired_keys:
        items.append({"level": "warn", "title": f"Retired app(s) still hold active keys: {', '.join(retired_keys)}",
                      "why": "Their calls are refused; revoke the keys so nothing keeps trying.", "go": "#apps", "names": retired_keys})
    orphans_offer = [t["name"] for t in tools if not t.get("apps")]
    if orphans_offer:
        items.append({"level": "info", "title": f"{len(orphans_offer)} tool(s) are offered to no app: {', '.join(orphans_offer)}",
                      "why": "Left behind when an app was deleted. Offer them to an app or delete them.", "go": "#tools", "names": orphans_offer})
    app_keys = {k["app"] for k in keys.list_keys() if not k.get("revoked_at")}
    without = [a for a in registry.apps() if a not in app_keys and registered.get(a, {}).get("status") != "retired"]
    if without:
        items.append({"level": "warn", "title": f"{len(without)} app(s) have no key: {', '.join(without)}",
                      "why": "Their calls are recorded as anonymous and will stop when keys become required.",
                      "go": "#apps", "names": without})
    report = registry.migration_report()
    if report and report.get("renamed"):
        report = {**report, "renamed": [r for r in report["renamed"] if registry.get_tool(r["to"]) or registry.get_skill(r["to"])]}
    if report and report.get("renamed"):
        items.append({"level": "warn", "title": f"{len(report['renamed'])} record(s) were renamed by the migration",
                      "why": "Same name, different content in two apps: " + ", ".join(
                          f"{r['from']} → {r['to']}" for r in report["renamed"]) + ". Decide which to keep.",
                      "go": "#tools", "names": [r["to"] for r in report["renamed"]]})
    return JSONResponse({"items": items})


@router.get("/admin/export")
async def admin_export(app: str | None = Query(None)):
    tools = registry.list_tools(app)
    skills = registry.list_skills(app)
    payload = {"version": registry.SCHEMA_VERSION, "app": app or "all", "tools": tools, "skills": skills}
    fname = f"registry-{app or 'all'}.json"
    return JSONResponse(payload, headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse(PAGE)


# ── Help: the manuals (app/help/<manual>/, README.md = the contents, one page per task, img/ beside them) and the
# documents of the documentation set, read-only, by name from a fixed list (as Cortex's api/docs.py) ──
HELP_DIR = Path(__file__).resolve().parent / "help"
DOC_DIR = Path(__file__).resolve().parents[1] / "documents"
DOCS = {"architecture": ("technical_architecture.md", "mcp-service — Technical Architecture"),
        "specification": ("console_specification.md", "mcp-service — Platform and Console Specification")}


@router.get("/admin/help/{manual}/{path:path}")
async def help_page(manual: str, path: str):
    base = (HELP_DIR / manual).resolve()
    target = (base / path).resolve()
    if manual not in ("manual", "guide") or not str(target).startswith(str(base)) or not target.is_file():
        raise HTTPException(status_code=404, detail="no such page")
    return FileResponse(target, media_type="text/markdown; charset=utf-8" if target.suffix == ".md" else None)


@router.get("/admin/docs/{name}")
async def document(name: str):
    entry = DOCS.get(name)
    if not entry or not (DOC_DIR / entry[0]).is_file():
        raise HTTPException(status_code=404, detail="no such document")
    return PlainTextResponse((DOC_DIR / entry[0]).read_text(encoding="utf-8"), media_type="text/markdown; charset=utf-8")


@router.get("/admin/fonts/{name}")
async def font(name: str):
    """Inter, self-hosted as Cortex does (the Banco CTT family; SIL Open Font License 1.1 beside it)."""
    target = (Path(__file__).resolve().parent / "static" / "fonts" / name).resolve()
    if name not in ("InterVariable.ttf", "Inter-LICENSE.txt") or not target.is_file():
        raise HTTPException(status_code=404, detail="no such file")
    return FileResponse(target, media_type="font/ttf" if name.endswith(".ttf") else "text/plain",
                        headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.get("/admin/i18n/{name}")
async def i18n(name: str):
    """The interface's dictionaries (static/pt.js: English -> European Portuguese), read by the page's translator."""
    target = (Path(__file__).resolve().parent / "static" / name).resolve()
    if name not in ("pt.js",) or not target.is_file():
        raise HTTPException(status_code=404, detail="no such file")
    return FileResponse(target, media_type="application/javascript")


@router.get("/admin/vendor/{name}")
async def vendor(name: str):
    """The page's vendored libraries (marked, DOMPurify: Cortex's copies), served beside it."""
    target = (Path(__file__).resolve().parent / "static" / "vendor" / name).resolve()
    if name not in ("marked.min.js", "purify.min.js") or not target.is_file():
        raise HTTPException(status_code=404, detail="no such file")
    return FileResponse(target, media_type="application/javascript")
