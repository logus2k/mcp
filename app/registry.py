"""JSON-persisted registry of tools + skills, scoped per app.

Tools are *declarative catalog entries* (name, schema, which built-in impl,
config, enabled) — the implementations ship with the service (app/toolimpl.py);
the UI never authors executable code. Skills are reusable instruction templates
(content + triggers) exposed over MCP as prompts.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

DATA_DIR = os.getenv("MCP_DATA_DIR", "/data")
REGISTRY_JSON = os.path.join(DATA_DIR, "registry.json")
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _key(app: str, name: str) -> str:
    return f"{app}/{name}"


# Seeded on first boot: the canonical first tool.
_WEB_SEARCH_SEED = {
    "name": "web_search",
    "app": "job2cool",
    "display_name": "Web Search",
    "description": "Search the web and return titles, URLs and snippets. "
                   "Backed by a stealth browser (Camoufox) in the isolated "
                   "websearch service.",
    "impl": "web_search",
    "tier": "read",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The web search query"},
            "max_results": {"type": "integer",
                            "description": "Maximum results to return (1-25)",
                            "default": 5},
        },
        "required": ["query"],
    },
    "config": {},
}


def _load() -> dict:
    with _LOCK:
        if not os.path.isfile(REGISTRY_JSON):
            return {"tools": {}, "skills": {}}
        try:
            with open(REGISTRY_JSON) as f:
                data = json.load(f)
            data.setdefault("tools", {})
            data.setdefault("skills", {})
            return data
        except Exception:  # noqa: BLE001
            return {"tools": {}, "skills": {}}


def _save(reg: dict) -> None:
    with _LOCK:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = REGISTRY_JSON + ".tmp"
        with open(tmp, "w") as f:
            json.dump(reg, f, indent=2)
        os.replace(tmp, REGISTRY_JSON)


_NGINX_REGISTER_SEED = {
    "name": "nginx_register_app",
    "app": "factory",
    "display_name": "Register app on the reverse proxy",
    "description": "Deterministically put a generated app on the domain nginx behind the shared "
                   "oauth2-proxy: writes a managed per-app location block for the given URL suffix and "
                   "port, validates the whole config (nginx -t, rolling back on failure) and reloads. "
                   "admin_only gates to the owner identity; unregister removes the block.",
    "impl": "nginx_register_app",
    "tier": "write",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "suffix": {"type": "string",
                       "description": "URL path the app is served at, e.g. 'restaurant-menu-manager'"},
            "port": {"type": "integer", "description": "the app's deployed host port"},
            "admin_only": {"type": "boolean", "default": False,
                           "description": "gate to the single owner identity (/oauth2/auth-admin)"},
            "public": {"type": "boolean", "default": False,
                       "description": "serve the base /suffix/ WITHOUT auth (open storefront); combine "
                                      "with admin_prefix to gate only the admin area"},
            "admin_prefix": {"type": "string",
                             "description": "a nested path under /suffix/ (e.g. 'admin') that IS gated; "
                                            "covers admin pages AND their APIs by prefix (no API leak)"},
            "unregister": {"type": "boolean", "default": False,
                           "description": "remove the app's route instead of adding it"},
        },
        "required": ["suffix"],
    },
    "config": {},
}


def seed() -> None:
    with _LOCK:
        reg = _load()
        changed = False
        for s in (_WEB_SEARCH_SEED, _NGINX_REGISTER_SEED):
            k = _key(s["app"], s["name"])
            if k not in reg["tools"]:
                rec = dict(s)
                rec["created_at"] = rec["updated_at"] = _now()
                reg["tools"][k] = rec
                changed = True
        if changed:
            _save(reg)


# ── tools ────────────────────────────────────────────────────────────────
def list_tools(app: str | None = None) -> list[dict]:
    return [t for t in _load()["tools"].values()
            if app is None or t.get("app") == app]


def get_tool(app: str, name: str) -> dict | None:
    return _load()["tools"].get(_key(app, name))


def put_tool(app: str, name: str, data: dict) -> dict:
    with _LOCK:
        reg = _load()
        k = _key(app, name)
        existing = reg["tools"].get(k)
        rec = {**(existing or {}), **data, "name": name, "app": app, "updated_at": _now()}
        rec.setdefault("created_at", rec["updated_at"])
        reg["tools"][k] = rec
        _save(reg)
        return rec


def delete_tool(app: str, name: str) -> bool:
    with _LOCK:
        reg = _load()
        k = _key(app, name)
        if k in reg["tools"]:
            del reg["tools"][k]
            _save(reg)
            return True
        return False


# ── skills ───────────────────────────────────────────────────────────────
def list_skills(app: str | None = None) -> list[dict]:
    return [s for s in _load()["skills"].values()
            if app is None or s.get("app") == app]


def get_skill(app: str, name: str) -> dict | None:
    return _load()["skills"].get(_key(app, name))


def put_skill(app: str, name: str, data: dict) -> dict:
    with _LOCK:
        reg = _load()
        k = _key(app, name)
        existing = reg["skills"].get(k)
        rec = {**(existing or {}), **data, "name": name, "app": app, "updated_at": _now()}
        rec.setdefault("created_at", rec["updated_at"])
        reg["skills"][k] = rec
        _save(reg)
        return rec


def delete_skill(app: str, name: str) -> bool:
    with _LOCK:
        reg = _load()
        k = _key(app, name)
        if k in reg["skills"]:
            del reg["skills"][k]
            _save(reg)
            return True
        return False
