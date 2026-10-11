"""JSON-persisted registry of tools and skills (schema version 2).

Tools are *declarative catalog entries* (name, schema, which built-in impl, config,
enabled, the apps they are offered to). The implementations ship with the service
(app/toolimpl*.py); the UI never authors executable code. Skills are reusable
instruction templates (content + arguments) exposed over MCP as prompts and as
``skill://`` resources.

A record is keyed by its ``name`` alone and carries ``apps``: the list of apps it is
offered to (console_specification.md section 4.4). Every write appends the new state to
``history.json`` (section 4.5) so any version can be shown, diffed and restored.

Version 1 registries (records keyed ``app/name``, one per app) are migrated on first
load: identical duplicates are merged and their app lists united; records that share a
name but differ are renamed ``name__app`` and listed in ``migration_report.json`` for a
human decision.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

SCHEMA_VERSION = 2
_LOCK = threading.RLock()

TOOL_DEFAULTS = {
    "display_name": "", "description": "", "impl": "", "tier": "read",
    "destructive": False, "idempotent": False, "enabled": True, "apps": [],
    "input_schema": {"type": "object"}, "output_schema": None, "config": {},
}
SKILL_DEFAULTS = {
    "display_name": "", "description": "", "content": "", "arguments": [],
    "apps": [], "tools": [], "tags": [], "enabled": True,
}
TIERS = ("read", "write")
APP_DEFAULTS = {"display_name": "", "description": "", "owner": "", "contact": "", "status": "active", "tags": []}
APP_STATUSES = ("active", "retired")


def data_dir() -> str:
    return os.getenv("MCP_DATA_DIR", "/data")


def _path(name: str) -> str:
    return os.path.join(data_dir(), name)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# ── seeds ────────────────────────────────────────────────────────────────────
_WEB_SEARCH_SEED = {
    "name": "web_search",
    "apps": ["job2cool"],
    "display_name": "Web Search",
    "description": "Search the web and return titles, URLs and snippets. "
                   "Backed by a stealth browser (Camoufox) in the isolated "
                   "websearch service.",
    "impl": "web_search",
    "tier": "read",
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
}

_NGINX_REGISTER_SEED = {
    "name": "nginx_register_app",
    "apps": ["factory"],
    "display_name": "Register app on the reverse proxy",
    "description": "Deterministically put a generated app on the domain nginx behind the shared "
                   "oauth2-proxy: writes a managed per-app location block for the given URL suffix and "
                   "port, validates the whole config (nginx -t, rolling back on failure) and reloads. "
                   "admin_only gates to the owner identity; unregister removes the block.",
    "impl": "nginx_register_app",
    "tier": "write",
    "destructive": True,
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
}

# The three starter skills (console_specification.md section 4.7): cross-cutting
# instructions several consumers must apply identically.
_SKILL_SEEDS = [
    {
        "name": "cite_with_tag",
        "display_name": "Cite knowledge-base passages with their tag",
        "description": "How to cite a passage returned by a knowledge-base tool so the page can "
                       "turn the citation into a button.",
        "content": "When you use a passage returned by {{kb_tool}}, cite it inline with its tag "
                   "exactly as the tool returned it, for example [markdown_chunk:3f9a1c…]. Never "
                   "invent a tag, never put a training, document or project id inside a tag, and "
                   "never cite a passage you did not read in this conversation.",
        "arguments": [{"name": "kb_tool", "description": "the knowledge-base search tool's name",
                       "required": False}],
        "apps": ["tutor", "slides"],
        "tools": ["search_knowledge_base", "kb_search"],
        "tags": ["citation", "knowledge-base"],
    },
    {
        "name": "pt_pt_style",
        "display_name": "European Portuguese",
        "description": "Write in the Portuguese of Portugal, never in Brazilian forms.",
        "content": "Write European Portuguese: the forms used in Portugal (tu/você as in Portugal, "
                   "'a fazer' rather than 'fazendo', Portuguese spelling), never Brazilian forms. Keep "
                   "product, team and document names exactly as the organisation writes them. When the "
                   "person writes in another language, answer in that language.",
        "arguments": [],
        "apps": ["tutor", "slides", "agent_runtime"],
        "tools": [],
        "tags": ["language"],
    },
    {
        "name": "ai_generated_disclosure",
        "display_name": "AI-generated disclosure",
        "description": "State once, plainly, that an answer was generated by a model and must be "
                       "checked before it is relied on.",
        "content": "When your answer will be read outside this conversation (sent, published, filed "
                   "or acted on by someone else), say once, plainly and without apology, that it was "
                   "generated by a language model and must be checked before it is relied on. Say it "
                   "once per answer, not per paragraph, and never remove it when asked to shorten.",
        "arguments": [],
        "apps": ["job2cool", "agent_runtime"],
        "tools": [],
        "tags": ["accountability"],
    },
]


# ── storage ──────────────────────────────────────────────────────────────────
def _empty() -> dict:
    return {"version": SCHEMA_VERSION, "tools": {}, "skills": {}, "apps": {}}


def _read_json(path: str, default):
    if not os.path.isfile(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001 — a corrupt file reads as empty; never crash the service
        return default


def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _load() -> dict:
    with _LOCK:
        data = _read_json(_path("registry.json"), None)
        if data is None:
            return _empty()
        if data.get("version") != SCHEMA_VERSION:
            data = _migrate_v1(data)
            _write_json(_path("registry.json"), data)
        data.setdefault("tools", {})
        data.setdefault("skills", {})
        data.setdefault("apps", {})
        return data


def _save(reg: dict) -> None:
    with _LOCK:
        reg["version"] = SCHEMA_VERSION
        _write_json(_path("registry.json"), reg)


# ── migration from version 1 ─────────────────────────────────────────────────
def _canon(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _tool_signature(rec: dict) -> str:
    """What must be equal for two per-app records to be one shared record."""
    config = dict(rec.get("config") or {})
    execution = config.pop("execution", "server")
    return _canon([rec.get("impl"), execution, rec.get("input_schema") or {}, config])


def _normalise_tool(rec: dict, apps: list[str]) -> dict:
    out = {**TOOL_DEFAULTS, **{k: v for k, v in rec.items() if k != "app"}}
    out["apps"] = sorted(set(apps))
    out.setdefault("version", 1)
    out.setdefault("created_at", _now())
    out.setdefault("updated_at", out["created_at"])
    return out


def _normalise_skill(rec: dict, apps: list[str]) -> dict:
    out = {**SKILL_DEFAULTS, **{k: v for k, v in rec.items() if k not in ("app", "triggers", "priority")}}
    out["apps"] = sorted(set(apps))
    out.setdefault("version", 1)
    out.setdefault("created_at", _now())
    out.setdefault("updated_at", out["created_at"])
    return out


def _migrate_v1(data: dict) -> dict:
    report = {"migrated_at": _now(), "merged": [], "renamed": [], "kept": []}
    out = _empty()
    for kind, signature, normalise in (("tools", _tool_signature, _normalise_tool),
                                       ("skills", lambda r: _canon(r.get("content", "")), _normalise_skill)):
        by_name: dict[str, list[dict]] = {}
        for key, rec in (data.get(kind) or {}).items():
            name = rec.get("name") or key.split("/", 1)[-1]
            app = rec.get("app") or key.split("/", 1)[0]
            by_name.setdefault(name, []).append({**rec, "name": name, "app": app})
        for name, recs in by_name.items():
            recs.sort(key=lambda r: r.get("created_at", ""))
            groups: dict[str, list[dict]] = {}
            for r in recs:
                groups.setdefault(signature(r), []).append(r)
            for i, group in enumerate(groups.values()):
                apps = [r["app"] for r in group]
                new_name = name if i == 0 else f"{name}__{apps[0]}"
                out[kind][new_name] = normalise({**group[0], "name": new_name}, apps)
                if i > 0:
                    report["renamed"].append({"kind": kind, "from": name, "to": new_name, "apps": apps,
                                              "why": "same name, different content: decide which to keep"})
                elif len(group) > 1:
                    report["merged"].append({"kind": kind, "name": name, "apps": apps})
                else:
                    report["kept"].append({"kind": kind, "name": name, "apps": apps})
    _write_json(_path("migration_report.json"), report)
    return out


def migration_report() -> dict | None:
    return _read_json(_path("migration_report.json"), None)


# ── history ──────────────────────────────────────────────────────────────────
def _append_history(kind: str, name: str, action: str, actor: str, record: dict | None) -> None:
    path = _path("history.json")
    hist = _read_json(path, [])
    hist.append({"kind": kind, "name": name, "action": action, "actor": actor, "ts": _now(),
                 "version": (record or {}).get("version"), "record": record})
    _write_json(path, hist)


def history(kind: str, name: str) -> list[dict]:
    return [h for h in _read_json(_path("history.json"), []) if h["kind"] == kind and h["name"] == name]


def seed() -> None:
    with _LOCK:
        reg = _load()
        changed = False
        for s in (_WEB_SEARCH_SEED, _NGINX_REGISTER_SEED):
            if s["name"] not in reg["tools"]:
                reg["tools"][s["name"]] = _normalise_tool(s, s["apps"])
                changed = True
        if not reg["skills"]:
            for s in _SKILL_SEEDS:
                reg["skills"][s["name"]] = _normalise_skill(s, s["apps"])
                changed = True
        # the application catalog (section 13): every app a record names has a record of its own; the first
        # load registers the ones that predate the catalog, so nothing disappears
        for name in _referenced_apps(reg):
            if name not in reg["apps"]:
                reg["apps"][name] = {**APP_DEFAULTS, "name": name, "display_name": name, "version": 1,
                                     "created_at": _now(), "updated_at": _now(),
                                     "description": "Registered automatically when the catalog was introduced."}
                changed = True
        if changed:
            _save(reg)


# ── tools ────────────────────────────────────────────────────────────────────
def list_tools(app: str | None = None) -> list[dict]:
    return [t for t in _load()["tools"].values() if app is None or app in t.get("apps", [])]


def get_tool(name: str) -> dict | None:
    return _load()["tools"].get(name)


def put_tool(name: str, data: dict, actor: str = "api", app: str | None = None) -> dict:
    """Create or update. ``data`` merges over the existing record. A caller that scopes by
    ``app`` (the REST face's ``?app=``) and sends no ``apps`` adds that app to the list."""
    with _LOCK:
        reg = _load()
        existing = reg["tools"].get(name)
        rec = {**TOOL_DEFAULTS, **(existing or {}), **data, "name": name}
        if "apps" not in data and app:
            rec["apps"] = sorted(set((existing or {}).get("apps", [])) | {app})
        rec["apps"] = sorted(set(rec.get("apps") or []))
        if rec["tier"] not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}")
        if not isinstance(rec.get("input_schema"), dict):
            raise ValueError("input_schema must be a JSON object")
        rec["version"] = int((existing or {}).get("version", 0)) + 1
        rec["updated_at"] = _now()
        rec.setdefault("created_at", rec["updated_at"])
        reg["tools"][name] = rec
        _save(reg)
        _append_history("tool", name, "update" if existing else "create", actor, rec)
        return rec


def delete_tool(name: str, actor: str = "api", app: str | None = None) -> bool:
    """Delete the record; with ``app`` and a record offered to other apps too, only
    withdraw it from that app."""
    with _LOCK:
        reg = _load()
        rec = reg["tools"].get(name)
        if not rec:
            return False
        if app and len(rec.get("apps", [])) > 1 and app in rec["apps"]:
            rec["apps"] = [a for a in rec["apps"] if a != app]
            rec["version"] = int(rec.get("version", 0)) + 1
            rec["updated_at"] = _now()
            _save(reg)
            _append_history("tool", name, "update", actor, rec)
            return True
        del reg["tools"][name]
        _save(reg)
        _append_history("tool", name, "delete", actor, None)
        return True


# ── skills ───────────────────────────────────────────────────────────────────
def list_skills(app: str | None = None) -> list[dict]:
    return [s for s in _load()["skills"].values() if app is None or app in s.get("apps", [])]


def get_skill(name: str) -> dict | None:
    return _load()["skills"].get(name)


def put_skill(name: str, data: dict, actor: str = "api", app: str | None = None) -> dict:
    with _LOCK:
        reg = _load()
        existing = reg["skills"].get(name)
        rec = {**SKILL_DEFAULTS, **(existing or {}), **data, "name": name}
        if "apps" not in data and app:
            rec["apps"] = sorted(set((existing or {}).get("apps", [])) | {app})
        rec["apps"] = sorted(set(rec.get("apps") or []))
        if not isinstance(rec.get("arguments"), list):
            raise ValueError("arguments must be a list of {name, description, required}")
        rec["version"] = int((existing or {}).get("version", 0)) + 1
        rec["updated_at"] = _now()
        rec.setdefault("created_at", rec["updated_at"])
        reg["skills"][name] = rec
        _save(reg)
        _append_history("skill", name, "update" if existing else "create", actor, rec)
        return rec


def delete_skill(name: str, actor: str = "api", app: str | None = None) -> bool:
    with _LOCK:
        reg = _load()
        rec = reg["skills"].get(name)
        if not rec:
            return False
        if app and len(rec.get("apps", [])) > 1 and app in rec["apps"]:
            rec["apps"] = [a for a in rec["apps"] if a != app]
            rec["version"] = int(rec.get("version", 0)) + 1
            rec["updated_at"] = _now()
            _save(reg)
            _append_history("skill", name, "update", actor, rec)
            return True
        del reg["skills"][name]
        _save(reg)
        _append_history("skill", name, "delete", actor, None)
        return True


def render_skill(skill: dict, arguments: dict | None) -> str:
    """The prompt text a client receives: ``{{name}}`` placeholders replaced by the
    arguments given (or an argument's default); others are left as written."""
    text = skill.get("content", "")
    values = {a["name"]: a.get("default") for a in skill.get("arguments", []) if a.get("default") is not None}
    values.update({k: v for k, v in (arguments or {}).items() if v is not None})
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


# ── restore ──────────────────────────────────────────────────────────────────
def restore(kind: str, name: str, version: int, actor: str = "api") -> dict:
    """Make a past version current again (a new version whose content is the old one)."""
    entries = [h for h in history(kind, name) if h.get("version") == version and h.get("record")]
    if not entries:
        raise KeyError(f"no version {version} of {kind} {name}")
    old = dict(entries[-1]["record"])
    for k in ("version", "created_at", "updated_at", "name"):
        old.pop(k, None)
    put = {"tool": put_tool, "skill": put_skill, "app": put_app}[kind]
    return put(name, old, actor=f"{actor} (restore v{version})")


def _referenced_apps(reg: dict) -> set[str]:
    names = set()
    for rec in list(reg["tools"].values()) + list(reg["skills"].values()):
        names.update(rec.get("apps", []))
    return names


def apps() -> list[str]:
    """Every app: the registered ones and any a record still names without a registration."""
    reg = _load()
    return sorted(set(reg["apps"]) | _referenced_apps(reg))


# ── the application catalog ──────────────────────────────────────────────────
def list_apps() -> list[dict]:
    return list(_load()["apps"].values())


def get_app(name: str) -> dict | None:
    return _load()["apps"].get(name)


def put_app(name: str, data: dict, actor: str = "api") -> dict:
    name = (name or "").strip()
    if not name or any(c for c in name if not (c.isalnum() or c in "-_")):
        raise ValueError("an app name is letters, digits, '-' and '_'")
    with _LOCK:
        reg = _load()
        existing = reg["apps"].get(name)
        rec = {**APP_DEFAULTS, **(existing or {}), **data, "name": name}
        if rec["status"] not in APP_STATUSES:
            raise ValueError(f"status must be one of {APP_STATUSES}")
        if not isinstance(rec.get("tags"), list):
            raise ValueError("tags must be a list")
        rec["display_name"] = rec.get("display_name") or name
        rec["version"] = int((existing or {}).get("version", 0)) + 1
        rec["updated_at"] = _now()
        rec.setdefault("created_at", rec["updated_at"])
        reg["apps"][name] = rec
        _save(reg)
        _append_history("app", name, "update" if existing else "create", actor, rec)
        return rec


def app_usage(name: str) -> dict:
    reg = _load()
    return {"tools": [t["name"] for t in reg["tools"].values() if name in t.get("apps", [])],
            "skills": [s["name"] for s in reg["skills"].values() if name in s.get("apps", [])]}


def delete_app(name: str, actor: str = "api", force: bool = False) -> bool:
    """Delete the record. With offers still naming the app, refuse unless ``force``: then the app is withdrawn
    from every tool and skill first."""
    with _LOCK:
        reg = _load()
        if name not in reg["apps"]:
            return False
        use = app_usage(name)
        if (use["tools"] or use["skills"]) and not force:
            raise ValueError(f"{name} is still offered {len(use['tools'])} tool(s) and {len(use['skills'])} skill(s); "
                             "withdraw them first, or delete with force")
        for kind in ("tools", "skills"):
            for rec in reg[kind].values():
                if name in rec.get("apps", []):
                    rec["apps"] = [a for a in rec["apps"] if a != name]
                    rec["version"] = int(rec.get("version", 0)) + 1
                    rec["updated_at"] = _now()
                    _append_history(kind[:-1], rec["name"], "update", actor, rec)
        del reg["apps"][name]
        _save(reg)
        _append_history("app", name, "delete", actor, None)
        return True


def unknown_apps(names: list[str]) -> list[str]:
    reg = _load()
    return [a for a in names if a not in reg["apps"]]
