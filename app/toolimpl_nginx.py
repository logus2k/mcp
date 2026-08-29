"""Deterministic reverse-proxy registration tool (MCP).

`nginx_register_app` is the ONE sanctioned, deterministic way to put a generated app on the domain proxy
behind the shared oauth2-proxy. It writes a MANAGED per-app location block (one file per suffix in the
proxy's `apps/` include dir), then VALIDATES the whole config (`nginx -t`) and RELOADS — rolling the file
back if validation fails. It never string-edits the main nginx.conf; the change is a single file the tool
owns, so it is idempotent and reversible. This replaces an agent hand-editing nginx with a validated tool.

Inputs: `suffix` (the URL path the app is served at, e.g. "restaurant-menu-manager") and `port` (the
app's deployed host port). `admin_only=true` gates to the single owner identity (/oauth2/auth-admin)
instead of any signed-in Google user (/oauth2/auth). `unregister=true` removes the app's block.

GATING SHAPE (public-vs-admin). By default the WHOLE `/suffix/` is gated (any signed-in Google user).
For an app with a PUBLIC surface plus a protected admin area, pass:
  * `public=true`      — the base `/suffix/` is served WITHOUT auth (the open storefront);
  * `admin_prefix="admin"` — a nested `/suffix/admin/` location that IS gated (admin_only ⇒ owner-only).
Gating is by PREFIX, so it covers both the admin PAGES and the admin API calls under that prefix — there
is no "protect the page but leave the mutating API open" leak. The app must serve its admin surface (pages
AND their endpoints) under that prefix for the gate to bind; a flat app with no admin surface just uses the
default whole-app gate or `public=true` for a fully-open app.
"""

from __future__ import annotations

import os
import re
import subprocess

#: proxy_server/conf mounted here (rw); the tool writes <PROXY_CONF_DIR>/apps/<suffix>.conf, which
#: nginx.conf includes via `include /etc/nginx/conf-host/apps/*.conf;`.
PROXY_CONF_DIR = os.environ.get("PROXY_CONF_DIR", "/proxy-conf")
PROXY_CONTAINER = os.environ.get("PROXY_CONTAINER", "proxy_server")
#: the proxy reaches host-published app ports via the docker host gateway.
APP_UPSTREAM_HOST = os.environ.get("APP_UPSTREAM_HOST", "host.docker.internal")

_SLUG_RE = re.compile(r"[^a-z0-9-]")


def _slug(s: str) -> str:
    s = _SLUG_RE.sub("-", (s or "").strip().strip("/").lower())
    return re.sub(r"-+", "-", s).strip("-")


def _location(match: str, port: int, gate: str | None, upstream_path: str = "/") -> str:
    """One nginx location block for `match` proxying to the app on `port`. `gate` is the oauth2-proxy
    auth_request endpoint (None ⇒ PUBLIC, no auth). `upstream_path` is the proxy_pass target URI: only the
    app SUFFIX is stripped, never a meaningful app path — the base strips `/suffix/` -> `/`, and an admin
    prefix strips `/suffix/admin/` -> `/admin/` (upstream_path='/admin/') so the app's own /admin routes
    (pages AND their APIs) still match. Getting this wrong would 404 every admin route."""
    lines = [f"location {match} {{"]
    if gate:
        lines += [f"    auth_request {gate};",
                  "    error_page 401 = /oauth2/sign_in;",
                  "    auth_request_set $auth_email $upstream_http_x_auth_request_email;"]
    lines += [f"    proxy_pass http://{APP_UPSTREAM_HOST}:{port}{upstream_path};",
              "    proxy_http_version 1.1;",
              "    client_max_body_size 50m;",
              "    proxy_set_header Host $host;",
              "    proxy_set_header X-Real-IP $remote_addr;",
              "    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
              "    proxy_set_header X-Forwarded-Proto $scheme;"]
    # only forward the identity header on gated locations (public locations have no authenticated user)
    email_val = "$auth_email" if gate else '""'
    lines.append(f"    proxy_set_header X-Auth-Request-Email {email_val};")
    lines += ["    proxy_read_timeout 600s;", "}"]
    return "\n".join(lines) + "\n"


def _block(suffix: str, port: int, admin_only: bool, public: bool = False,
           admin_prefix: str | None = None) -> str:
    """Render the managed conf for one app. Default: the whole `/suffix/` is gated. With `public=True`
    the base is open; with `admin_prefix` a MORE-SPECIFIC `/suffix/<prefix>/` location is gated (nginx
    routes the longest `^~` prefix first, so admin paths hit the gated block and the rest stay public)."""
    admin_gate = "/oauth2/auth-admin" if admin_only else "/oauth2/auth"
    header = (f"# MANAGED by the MCP nginx_register_app tool — do not edit by hand. app suffix: {suffix}"
              f" (public={public}, admin_prefix={admin_prefix or '-'}, admin_only={admin_only})\n")
    blocks = []
    # gated admin sub-path FIRST (more specific ^~ prefix wins regardless of file order, but keep it clear)
    if admin_prefix:
        ap = _slug(admin_prefix)
        if ap:
            # strip only the app suffix: /suffix/admin/x -> app /admin/x (keep the admin prefix)
            blocks.append(_location(f"^~ /{suffix}/{ap}/", port, admin_gate, upstream_path=f"/{ap}/"))
    # base location: public (ungated) or gated per admin_only
    base_gate = None if public else admin_gate
    blocks.append(_location(f"^~ /{suffix}/", port, base_gate))
    return header + "\n".join(blocks)


def _nginx(*argv: str, timeout: float = 30) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "exec", PROXY_CONTAINER, "nginx", *argv],
                          capture_output=True, text=True, timeout=timeout)


async def nginx_register_app(args: dict, config: dict) -> dict:
    suffix = _slug(str(args.get("suffix", "")))
    unregister = bool(args.get("unregister", False))
    admin_only = bool(args.get("admin_only", False))
    public = bool(args.get("public", False))
    admin_prefix = args.get("admin_prefix") or None
    if not suffix:
        return {"ok": False, "error": "invalid or empty suffix"}
    apps_dir = os.path.join(PROXY_CONF_DIR, "apps")
    os.makedirs(apps_dir, exist_ok=True)
    path = os.path.join(apps_dir, f"{suffix}.conf")
    prev = open(path, encoding="utf-8").read() if os.path.exists(path) else None

    if unregister:
        if prev is None:
            return {"ok": True, "route": f"/{suffix}/", "unregistered": True, "note": "was not registered"}
        os.remove(path)
    else:
        try:
            port = int(args.get("port"))
        except (TypeError, ValueError):
            return {"ok": False, "error": "port must be an integer"}
        if not (1 <= port <= 65535):
            return {"ok": False, "error": "port out of range"}
        with open(path, "w", encoding="utf-8") as f:
            f.write(_block(suffix, port, admin_only, public=public, admin_prefix=admin_prefix))

    # VALIDATE the whole config; on failure roll the file back so the proxy is never left broken.
    t = _nginx("-t")
    if t.returncode != 0:
        if prev is None:
            if os.path.exists(path):
                os.remove(path)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(prev)
        return {"ok": False, "error": "nginx -t failed; change rolled back",
                "detail": (t.stderr or t.stdout)[-600:]}

    r = _nginx("-s", "reload")
    ok = r.returncode == 0
    out = {"ok": ok, "route": f"/{suffix}/", "validated": True, "reloaded": ok,
           "admin_only": admin_only, "public": public,
           "admin_route": (f"/{suffix}/{_slug(admin_prefix)}/" if admin_prefix else None),
           "unregistered": unregister}
    if not unregister:
        out["port"] = int(args.get("port"))
    if not ok:
        out["detail"] = (r.stderr or r.stdout)[-400:]
    return out
