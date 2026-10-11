"""OAuth 2.1 for MCP clients (console_specification.md section 12).

The service is the MCP **resource server** and hosts its own **authorization server**, the
shape the MCP specification (2025-06-18) prescribes for remote HTTP servers:

* RFC 8414 metadata at ``/.well-known/oauth-authorization-server`` and RFC 9728 metadata at
  ``/.well-known/oauth-protected-resource`` (also path-aware, per app);
* RFC 7591 dynamic client registration at ``/oauth/register`` (public clients, PKCE);
* the authorization code flow with PKCE S256 at ``/oauth/authorize`` — the person signs
  in through the domain proxy (Microsoft Entra ID), as everywhere else here, and a consent
  page asks what the client may do; ``/oauth/decision`` records the answer;
* ``/oauth/token`` exchanges the code (or a refresh token) for a signed access token;
  ``/oauth/revoke`` ends a refresh token;
* the **client credentials** grant for programs: a *machine client* an administrator registers in the
  console, bound to an app of the catalog and to the scopes it may use; its token acts as the app,
  with no person behind it, and is recorded as ``client:<id>``. Never issued through dynamic
  registration: a machine speaks for an app, and nobody consents on its behalf.

Access tokens are JWTs (HS256, a key kept in ``data/oauth_signing.key``) carrying the
person (``sub``), the client, the scopes and the audience (the MCP endpoint). Scopes:
``tools:read``, ``tools:write``, ``admin``. State lives in ``data/oauth.json``.
No regular expressions: redirect URIs and PKCE verifiers are checked with string operations.
"""
from __future__ import annotations

import base64
import hashlib
import html
import os
import secrets
import threading
import time
from urllib.parse import urlencode, urlparse

import jwt

from app import registry

SCOPES = ("tools:read", "tools:write", "admin")
DEFAULT_SCOPE = "tools:read"
CODE_TTL = 600            # s: an authorization code, and a pending consent
ACCESS_TTL = 3600         # s
REFRESH_TTL = 30 * 86400  # s
MAX_CLIENTS = 200
_LOCK = threading.RLock()
_VERIFIER_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


# ── configuration ────────────────────────────────────────────────────────────
def public_url() -> str:
    """Where clients reach the service: the issuer. Internal address when unset (tests, dev)."""
    return (os.getenv("MCP_PUBLIC_URL", "") or "http://mcp-service:8080").rstrip("/")


def _path(name: str) -> str:
    return os.path.join(registry.data_dir(), name)


def signing_key() -> str:
    key = os.getenv("MCP_OAUTH_SIGNING_KEY", "").strip()
    if key:
        return key
    path = _path("oauth_signing.key")
    if os.path.isfile(path):
        with open(path) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    os.makedirs(registry.data_dir(), exist_ok=True)
    with open(path, "w") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


# ── state ────────────────────────────────────────────────────────────────────
def _load() -> dict:
    data = registry._read_json(_path("oauth.json"), {})
    for k in ("clients", "codes", "refresh", "pending"):
        data.setdefault(k, {})
    return data


def _save(data: dict) -> None:
    registry._write_json(_path("oauth.json"), data)


def _prune(data: dict) -> None:
    now = time.time()
    for k in ("codes", "pending"):
        data[k] = {i: v for i, v in data[k].items() if v.get("exp", 0) > now}
    data["refresh"] = {i: v for i, v in data["refresh"].items() if v.get("exp", 0) > now and not v.get("revoked")}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# ── metadata ─────────────────────────────────────────────────────────────────
def authorization_server_metadata() -> dict:
    base = public_url()
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "revocation_endpoint": f"{base}/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token", "client_credentials"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "revocation_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": list(SCOPES),
        "service_documentation": f"{base}/admin#help-guide/08-oauth.md",
    }


def protected_resource_metadata(app: str | None = None) -> dict:
    base = public_url()
    return {
        "resource": f"{base}/mcp/{app}/" if app else f"{base}/mcp/",
        "authorization_servers": [base],
        "bearer_methods_supported": ["header"],
        "scopes_supported": list(SCOPES),
        "resource_name": f"MCP Server · {app}" if app else "MCP Server",
        "resource_documentation": f"{base}/admin#help-guide/08-oauth.md",
    }


def www_authenticate(error: str | None = None, description: str | None = None) -> str:
    parts = [f'realm="mcp-service"', f'resource_metadata="{public_url()}/.well-known/oauth-protected-resource"']
    if error:
        parts.append(f'error="{error}"')
    if description:
        # an HTTP header is ASCII: drop anything else (the ellipsis in the messages), and quotes
        clean = description.replace(chr(34), "").encode("ascii", "ignore").decode().strip()
        parts.append(f'error_description="{clean}"')
    return "Bearer " + ", ".join(parts)


# ── errors ───────────────────────────────────────────────────────────────────
class OAuthError(Exception):
    def __init__(self, error: str, description: str, status: int = 400):
        super().__init__(description)
        self.error, self.description, self.status = error, description, status

    def body(self) -> dict:
        return {"error": self.error, "error_description": self.description}


# ── clients (RFC 7591) ───────────────────────────────────────────────────────
def _valid_redirect(uri: str) -> bool:
    try:
        u = urlparse(uri)
    except ValueError:
        return False
    if u.fragment or not u.netloc:
        return False
    if u.scheme == "https":
        return True
    # loopback redirects for native clients (Claude Code and the like): http://localhost:<any port>/...
    return u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1", "::1")


def register_client(body: dict) -> dict:
    uris = body.get("redirect_uris")
    if not isinstance(uris, list) or not uris or not all(isinstance(u, str) and _valid_redirect(u) for u in uris):
        raise OAuthError("invalid_redirect_uri", "redirect_uris must list https URLs or http://localhost URLs")
    method = body.get("token_endpoint_auth_method") or "none"
    if method not in ("none", "client_secret_post"):
        raise OAuthError("invalid_client_metadata", "token_endpoint_auth_method must be none or client_secret_post")
    grants = body.get("grant_types") or ["authorization_code", "refresh_token"]
    if any(g not in ("authorization_code", "refresh_token") for g in grants):
        raise OAuthError("invalid_client_metadata", "grant_types may hold authorization_code and refresh_token; a "
                         "client_credentials client is registered by an administrator in the console, bound to an app")
    with _LOCK:
        data = _load()
        _prune(data)
        if len(data["clients"]) >= MAX_CLIENTS:
            raise OAuthError("invalid_client_metadata", "too many registered clients; revoke some in the console")
        client_id = "mcpc_" + secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(32) if method == "client_secret_post" else None
        rec = {
            "client_id": client_id,
            "client_name": str(body.get("client_name") or "")[:120] or "MCP client",
            "redirect_uris": uris,
            "grant_types": grants,
            "token_endpoint_auth_method": method,
            "client_uri": str(body.get("client_uri") or "")[:300],
            "secret_hash": _sha(secret) if secret else None,
            "kind": "person",
            "created_at": registry._now(),
            "last_used_at": None,
        }
        data["clients"][client_id] = rec
        _save(data)
    out = {k: v for k, v in rec.items() if k not in ("secret_hash", "last_used_at")}
    out["client_id_issued_at"] = int(time.time())
    if secret:
        out["client_secret"] = secret
        out["client_secret_expires_at"] = 0
    return out


MACHINE_SCOPES = ("tools:read", "tools:write")


def register_machine_client(app: str, name: str, scopes: list[str] | None) -> dict:
    """A client that speaks for an app of the catalog (the console, administrators only): id and secret, the
    secret shown once. Its tokens come from the client credentials grant."""
    rec_app = registry.get_app(app)
    if not rec_app:
        raise OAuthError("invalid_client_metadata", f"'{app}' is not a registered app")
    if rec_app.get("status") == "retired":
        raise OAuthError("invalid_client_metadata", f"'{app}' is retired")
    scopes = [s for s in (scopes or ["tools:read"]) if s]
    bad = [s for s in scopes if s not in MACHINE_SCOPES]
    if bad:
        raise OAuthError("invalid_scope", f"a machine client may hold {', '.join(MACHINE_SCOPES)}; not {', '.join(bad)}")
    with _LOCK:
        data = _load()
        if len(data["clients"]) >= MAX_CLIENTS:
            raise OAuthError("invalid_client_metadata", "too many registered clients; remove some in the console")
        client_id = "mcpm_" + secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(32)
        rec = {
            "client_id": client_id, "client_name": (name or "").strip()[:120] or app, "redirect_uris": [],
            "grant_types": ["client_credentials"], "token_endpoint_auth_method": "client_secret_post",
            "client_uri": "", "secret_hash": _sha(secret), "kind": "machine", "app": app,
            "scopes": sorted(set(scopes)), "created_at": registry._now(), "last_used_at": None,
        }
        data["clients"][client_id] = rec
        _save(data)
    return {k: v for k, v in rec.items() if k != "secret_hash"} | {"client_secret": secret}


def list_clients(app: str | None = None, kind: str | None = None) -> list[dict]:
    data = _load()
    out = []
    for c in data["clients"].values():
        if app and c.get("app") != app:
            continue
        if kind and c.get("kind", "person") != kind:
            continue
        tokens = sum(1 for r in data["refresh"].values() if r["client_id"] == c["client_id"] and not r.get("revoked"))
        out.append({k: v for k, v in c.items() if k != "secret_hash"} | {"active_refresh_tokens": tokens,
                                                                          "kind": c.get("kind", "person")})
    return out


def delete_client(client_id: str) -> bool:
    with _LOCK:
        data = _load()
        if client_id not in data["clients"]:
            return False
        del data["clients"][client_id]
        data["refresh"] = {i: v for i, v in data["refresh"].items() if v["client_id"] != client_id}
        data["codes"] = {i: v for i, v in data["codes"].items() if v["client_id"] != client_id}
        _save(data)
        return True


def _client(data: dict, client_id: str | None) -> dict:
    c = data["clients"].get(client_id or "")
    if not c:
        raise OAuthError("invalid_client", "unknown client_id", 401)
    return c


def _authenticate_client(data: dict, client_id: str | None, client_secret: str | None) -> dict:
    c = _client(data, client_id)
    if c["token_endpoint_auth_method"] == "client_secret_post":
        if not client_secret or _sha(client_secret) != c["secret_hash"]:
            raise OAuthError("invalid_client", "client authentication failed", 401)
    return c


# ── authorization (the code flow with PKCE) ──────────────────────────────────
def _scopes(requested: str | None) -> list[str]:
    asked = [s for s in (requested or "").split() if s]
    if not asked:
        return [DEFAULT_SCOPE]
    bad = [s for s in asked if s not in SCOPES]
    if bad:
        raise OAuthError("invalid_scope", f"unknown scope(s): {', '.join(bad)}; supported: {', '.join(SCOPES)}")
    return asked


def begin_authorization(params: dict, user: str) -> dict:
    """Validate an authorize request for the signed-in ``user``; keep it pending for the consent page."""
    client_id, redirect_uri = params.get("client_id"), params.get("redirect_uri")
    with _LOCK:
        data = _load()
        _prune(data)
        c = _client(data, client_id)
        if redirect_uri not in c["redirect_uris"]:
            raise OAuthError("invalid_request", "redirect_uri is not registered for this client")
        if params.get("response_type") != "code":
            raise OAuthError("unsupported_response_type", "response_type must be code")
        challenge = params.get("code_challenge") or ""
        if params.get("code_challenge_method", "S256") != "S256" or len(challenge) < 43:
            raise OAuthError("invalid_request", "PKCE with code_challenge_method S256 is required")
        scopes = _scopes(params.get("scope"))
        resource = params.get("resource") or f"{public_url()}/mcp/"
        if not resource.startswith(public_url()) and not resource.startswith("http://mcp-service:8080"):
            raise OAuthError("invalid_target", f"resource must be this server's MCP endpoint ({public_url()}/mcp/…)")
        rid = secrets.token_urlsafe(24)
        data["pending"][rid] = {
            "client_id": client_id, "client_name": c["client_name"], "redirect_uri": redirect_uri,
            "code_challenge": challenge, "scope": " ".join(scopes), "resource": resource,
            "state": params.get("state") or "", "user": user, "exp": time.time() + CODE_TTL,
        }
        _save(data)
        return {"rid": rid, **data["pending"][rid]}


def decide(rid: str, allow: bool, user: str) -> str:
    """The person's answer on the consent page: the URL to send them to."""
    with _LOCK:
        data = _load()
        _prune(data)
        p = data["pending"].pop(rid, None)
        if not p or p["user"] != user:
            raise OAuthError("invalid_request", "this authorization request has expired; start again from the client")
        if not allow:
            _save(data)
            return _redirect(p["redirect_uri"], {"error": "access_denied", "state": p["state"]})
        code = secrets.token_urlsafe(32)
        data["codes"][code] = {k: p[k] for k in ("client_id", "redirect_uri", "code_challenge", "scope", "resource", "user")} | {"exp": time.time() + CODE_TTL}
        _save(data)
        return _redirect(p["redirect_uri"], {"code": code, "state": p["state"]})


def _redirect(uri: str, params: dict) -> str:
    params = {k: v for k, v in params.items() if v}
    return uri + ("&" if "?" in uri else "?") + urlencode(params)


# ── tokens ───────────────────────────────────────────────────────────────────
def _pkce_ok(verifier: str | None, challenge: str) -> bool:
    if not verifier or not (43 <= len(verifier) <= 128) or any(ch not in _VERIFIER_CHARS for ch in verifier):
        return False
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode() == challenge


def _issue(data: dict, client_id: str, user: str, scope: str, resource: str) -> dict:
    now = int(time.time())
    access = jwt.encode({"iss": public_url(), "sub": user, "aud": resource, "client_id": client_id, "scope": scope,
                         "iat": now, "exp": now + ACCESS_TTL, "jti": secrets.token_hex(8)}, signing_key(), algorithm="HS256")
    refresh = "mcpr_" + secrets.token_urlsafe(32)
    data["refresh"][_sha(refresh)] = {"client_id": client_id, "user": user, "scope": scope, "resource": resource,
                                      "exp": time.time() + REFRESH_TTL, "revoked": False, "created_at": registry._now()}
    data["clients"][client_id]["last_used_at"] = registry._now()
    return {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TTL, "refresh_token": refresh, "scope": scope}


def token(form: dict) -> dict:
    grant = form.get("grant_type")
    with _LOCK:
        data = _load()
        _prune(data)
        if grant == "authorization_code":
            c = _authenticate_client(data, form.get("client_id"), form.get("client_secret"))
            rec = data["codes"].pop(form.get("code") or "", None)
            if not rec or rec["client_id"] != c["client_id"]:
                _save(data)
                raise OAuthError("invalid_grant", "unknown, used or expired authorization code")
            if rec["redirect_uri"] != form.get("redirect_uri"):
                _save(data)
                raise OAuthError("invalid_grant", "redirect_uri does not match the authorization request")
            if not _pkce_ok(form.get("code_verifier"), rec["code_challenge"]):
                _save(data)
                raise OAuthError("invalid_grant", "PKCE verification failed")
            out = _issue(data, c["client_id"], rec["user"], rec["scope"], rec["resource"])
            _save(data)
            return out
        if grant == "refresh_token":
            c = _authenticate_client(data, form.get("client_id"), form.get("client_secret"))
            key = _sha(form.get("refresh_token") or "")
            rec = data["refresh"].pop(key, None)
            if not rec or rec["client_id"] != c["client_id"] or rec.get("revoked"):
                _save(data)
                raise OAuthError("invalid_grant", "unknown, revoked or expired refresh token")
            scope = rec["scope"]
            if form.get("scope"):
                asked = _scopes(form["scope"])
                if any(s not in scope.split() for s in asked):
                    _save(data)
                    raise OAuthError("invalid_scope", "a refresh may narrow the scope, not widen it")
                scope = " ".join(asked)
            out = _issue(data, c["client_id"], rec["user"], scope, rec["resource"])   # rotation: the old one is gone
            _save(data)
            return out
        if grant == "client_credentials":
            c = _authenticate_client(data, form.get("client_id"), form.get("client_secret"))
            if c.get("kind") != "machine" or not c.get("app"):
                raise OAuthError("unauthorized_client", "only a machine client registered for an app may use client_credentials")
            rec_app = registry.get_app(c["app"])
            if not rec_app or rec_app.get("status") == "retired":
                raise OAuthError("unauthorized_client", f"app '{c['app']}' is retired or gone")
            allowed = c.get("scopes") or ["tools:read"]
            asked = [x for x in (form.get("scope") or "").split() if x] or allowed
            bad = [x for x in asked if x not in allowed]
            if bad:
                raise OAuthError("invalid_scope", f"this client may not use: {', '.join(bad)}")
            now = int(time.time())
            access = jwt.encode({"iss": public_url(), "sub": f"app:{c['app']}", "app": c["app"], "aud": f"{public_url()}/mcp/{c['app']}/",
                                 "client_id": c["client_id"], "scope": " ".join(asked), "iat": now, "exp": now + ACCESS_TTL,
                                 "jti": secrets.token_hex(8)}, signing_key(), algorithm="HS256")
            c["last_used_at"] = registry._now()
            _save(data)
            # no refresh token: the client asks again with its credentials (OAuth 2.1 section 4.2)
            return {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TTL, "scope": " ".join(asked)}
        raise OAuthError("unsupported_grant_type", "grant_type must be authorization_code, refresh_token or client_credentials")


def revoke(form: dict) -> None:
    with _LOCK:
        data = _load()
        c = _authenticate_client(data, form.get("client_id"), form.get("client_secret"))
        key = _sha(form.get("token") or "")
        rec = data["refresh"].get(key)
        if rec and rec["client_id"] == c["client_id"]:
            rec["revoked"] = True
        _save(data)      # an unknown token is not an error (RFC 7009)


def verify_access_token(token_text: str) -> dict | None:
    """The claims of a valid access token this server issued, else None."""
    try:
        claims = jwt.decode(token_text, signing_key(), algorithms=["HS256"], issuer=public_url(),
                            options={"verify_aud": False, "require": ["exp", "sub", "client_id", "scope"]})
    except jwt.PyJWTError:
        return None
    aud = claims.get("aud") or ""
    if not (aud.startswith(public_url()) or aud.startswith("http://mcp-service:8080")):
        return None
    if claims.get("client_id") not in _load()["clients"]:      # a removed client's tokens die with it
        return None
    return claims


def looks_like_jwt(token_text: str) -> bool:
    return token_text.count(".") == 2 and token_text.startswith("eyJ")


# ── the consent page ─────────────────────────────────────────────────────────
_SCOPE_TEXT = {
    "tools:read": "use read-tier tools (searches, fetches, sensors) as you",
    "tools:write": "use write-tier tools, which change things outside this service, as you (administrators only)",
    "admin": "administer the catalog as you (administrators only)",
}


def consent_page(p: dict, base_path: str) -> str:
    """The Banco CTT-styled page asking the signed-in person to allow or deny the client."""
    scopes = "".join(f"<li>{html.escape(_SCOPE_TEXT.get(s, s))}</li>" for s in p["scope"].split())
    app = p["resource"].rstrip("/").split("/mcp/")[-1] if "/mcp/" in p["resource"] else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCP Server · Allow {html.escape(p['client_name'])}?</title>
<style>
:root {{ --primary:#E00024; --surface:#fff; --page:#F7F9FC; --text:#000; --weak:#666; --divider:#E4E9F2; --field:#F1F4F8; color-scheme: light; }}
@media (prefers-color-scheme: dark) {{ :root {{ --surface:#1A1E26; --page:#12151B; --text:#F1F4F8; --weak:#C5CEE0; --divider:#2C3340; --field:#242A35; color-scheme: dark; }} }}
body {{ margin:0; font:400 14px/20px Inter, system-ui, sans-serif; color:var(--text); background:var(--page); display:grid; place-items:center; min-height:100vh; padding:16px; box-sizing:border-box; }}
.card {{ background:var(--surface); border:1px solid var(--divider); border-radius:10px; padding:32px; width:min(100%, 480px); }}
h1 {{ font-size:20px; line-height:24px; margin:0 0 8px; }} p {{ margin:0 0 12px; color:var(--weak); }} ul {{ margin:0 0 16px; padding-left:20px; }} li {{ margin:4px 0; }}
.who {{ background:var(--field); border-radius:6px; padding:10px 12px; margin:0 0 16px; }}
.row {{ display:flex; gap:8px; }} button {{ font:inherit; height:40px; padding:0 16px; border-radius:6px; border:1px solid var(--divider); background:var(--surface); color:var(--text); cursor:pointer; }}
button.primary {{ background:var(--primary); border-color:var(--primary); color:#fff; font-weight:700; }}
small {{ color:var(--weak); }}
</style></head><body><form class="card" method="post" action="{html.escape(base_path)}/oauth/decision">
<h1>Allow <span>{html.escape(p['client_name'])}</span> to use MCP Server?</h1>
<p>The client asks to act for you{(' on app <b>' + html.escape(app) + '</b>') if app else ''}. It would be able to:</p>
<ul>{scopes}</ul>
<div class="who">Signed in as <b>{html.escape(p['user'])}</b></div>
<input type="hidden" name="rid" value="{html.escape(p['rid'])}">
<div class="row"><button class="primary" name="decision" value="allow">Allow</button><button name="decision" value="deny">Deny</button></div>
<p style="margin-top:16px"><small>Every call the client makes is recorded under your address. You can revoke its access in the console, Settings › OAuth clients.</small></p>
</form></body></html>"""
