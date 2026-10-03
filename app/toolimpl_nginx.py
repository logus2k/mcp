"""Deterministic reverse-proxy registration tool (MCP).

`nginx_register_app` is the ONE sanctioned, deterministic way to put a generated app on the domain proxy
behind the shared oauth2-proxy. It writes a MANAGED per-app location block (one file per suffix in the
proxy's conf/ dir as route-<suffix>.conf), then VALIDATES the whole config (`nginx -t`) and RELOADS — rolling the file
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

#: proxy_server/conf mounted here (rw); the tool writes <PROXY_CONF_DIR>/route-<suffix>.conf,
#: which nginx.conf includes via `include /etc/nginx/conf-host/route-*.conf;` — one flat
#: directory, one file per route, so adding a route never rewrites a shared file.
PROXY_CONF_DIR = os.environ.get("PROXY_CONF_DIR", "/proxy-conf")
PROXY_CONTAINER = os.environ.get("PROXY_CONTAINER", "proxy_server")
#: the proxy reaches host-published app ports via the docker host gateway.
APP_UPSTREAM_HOST = os.environ.get("APP_UPSTREAM_HOST", "host.docker.internal")

_SLUG_RE = re.compile(r"[^a-z0-9-]")


def _slug(s: str) -> str:
    s = _SLUG_RE.sub("-", (s or "").strip().strip("/").lower())
    return re.sub(r"-+", "-", s).strip("-")


def _upstream_var(suffix: str) -> str:
    """The nginx variable name holding a container upstream, e.g. $devai_analyst_upstream."""
    return "$" + _slug(suffix).replace("-", "_") + "_upstream"


def _location(match: str, port: int, gate: str | None, upstream_path: str = "/",
              upstream: str | None = None, suffix: str = "") -> str:
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
    if upstream:
        # A CONTAINER upstream, held in a variable. nginx resolves a literal
        # proxy_pass host at CONFIG-PARSE TIME, so a container that is down
        # takes the whole proxy with it; via a variable it is resolved per
        # request and only this route 502s.
        #
        # The cost is that a variable proxy_pass passes the FULL URI — nginx
        # strips the location prefix only for a literal proxy_pass carrying a
        # URI — so the prefix is removed with an explicit rewrite. This is the
        # shape the hand-written Dev.AI routes already use.
        variable = _upstream_var(suffix)
        prefix = match.split(" ", 1)[-1].rstrip("/")
        lines += [f'    set {variable} "http://{upstream}";',
                  f"    rewrite ^{prefix}/(.*)$ {upstream_path}$1 break;",
                  f"    proxy_pass {variable};",
                  "    proxy_http_version 1.1;"]
    else:
        lines += [f"    proxy_pass http://{APP_UPSTREAM_HOST}:{port}{upstream_path};",
                  "    proxy_http_version 1.1;"]
    lines += [
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


#: The oauth2-proxy endpoints this proxy actually defines. A gate that does not
#: exist would fail `nginx -t` and be rolled back, but failing HERE names the
#: mistake instead of returning a validation error to unpick.
GATES = {
    "user": "/oauth2/auth",            # any signed-in Google identity
    "admin": "/oauth2/auth-admin",     # the single owner identity
    "devops": "/oauth2/auth-devops",
    "devai": "/oauth2/auth-devai",     # the factory's own console and agents
}


def resolve_gate(gate: str | None, admin_only: bool) -> str | None:
    """Which auth_request endpoint a location uses, or None for public.

    `gate` is the explicit choice and wins; `admin_only` remains as the older,
    narrower way of saying `gate="admin"`. A full path is accepted as-is so a
    gate added to the proxy later needs no change here.
    """
    if gate:
        name = str(gate).strip()
        if name.startswith("/"):
            return name
        if name not in GATES:
            raise ValueError(f"unknown gate {name!r}; known: {', '.join(sorted(GATES))}, "
                             "or pass a full path such as /oauth2/auth-devai")
        return GATES[name]
    return GATES["admin"] if admin_only else GATES["user"]


def _block(suffix: str, port: int, admin_only: bool, public: bool = False,
           admin_prefix: str | None = None, gate: str | None = None,
           upstream: str | None = None) -> str:
    """Render the managed conf for one app. Default: the whole `/suffix/` is gated. With `public=True`
    the base is open; with `admin_prefix` a MORE-SPECIFIC `/suffix/<prefix>/` location is gated (nginx
    routes the longest `^~` prefix first, so admin paths hit the gated block and the rest stay public)."""
    admin_gate = resolve_gate(gate, admin_only)
    header = (f"# MANAGED by the MCP nginx_register_app tool — do not edit by hand. app suffix: {suffix}"
              f" (public={public}, admin_prefix={admin_prefix or '-'}, admin_only={admin_only}"
              f", gate={admin_gate or 'none'}"
              f", upstream={upstream or f'{APP_UPSTREAM_HOST}:{port}'})\n")
    blocks = []
    # gated admin sub-path FIRST (more specific ^~ prefix wins regardless of file order, but keep it clear)
    if admin_prefix:
        ap = _slug(admin_prefix)
        if ap:
            # strip only the app suffix: /suffix/admin/x -> app /admin/x (keep the admin prefix)
            blocks.append(_location(f"^~ /{suffix}/{ap}/", port, admin_gate,
                                    upstream_path=f"/{ap}/", upstream=upstream,
                                    suffix=f"{suffix}-{ap}"))
    # base location: public (ungated) or gated per admin_only
    base_gate = None if public else admin_gate
    blocks.append(_location(f"^~ /{suffix}/", port, base_gate,
                            upstream=upstream, suffix=suffix))
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
    #: Which oauth2-proxy endpoint gates this route. See GATES.
    gate = args.get("gate") or None
    #: A CONTAINER upstream as "name:port" (e.g. "devai-analyst:8796"), reached
    #: on the docker network rather than through the host gateway. Resolved per
    #: request, so a container that is down 502s its own route instead of
    #: stopping nginx from starting.
    upstream = args.get("upstream") or None
    if not suffix:
        return {"ok": False, "error": "invalid or empty suffix"}
    # One file per route, FLAT in conf/, beside nginx.conf. The `route-` prefix
    # is load-bearing: nginx.conf includes `route-*.conf` from this same
    # directory, and a bare `*.conf` glob would match nginx.conf itself and
    # recurse ("events directive is not allowed here" — measured).
    path = os.path.join(PROXY_CONF_DIR, f"route-{suffix}.conf")
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
            try:
                f.write(_block(suffix, port, admin_only, public=public,
                               admin_prefix=admin_prefix, gate=gate,
                               upstream=upstream))
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}

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
