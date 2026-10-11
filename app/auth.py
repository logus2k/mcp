"""Who is calling, and whether they may (console_specification.md sections 4.1 and 4.10).

Four kinds of caller:
* ``admin``: the admin bearer token (``MCP_ADMIN_TOKEN``), or a person signed in through
  the domain proxy (Microsoft Entra ID via oauth2-proxy-entra) whom the proxy admitted and
  who is on ``MCP_ADMIN_EMAILS`` (or anyone the proxy admitted, when that list is empty).
  Recorded as ``console`` for the token, or as the person's address.
* ``person``: signed in through the proxy but not an admin: reads, and read-tier tools.
* ``key``: an app key (``mcpk_…``), bound to one app. Recorded by key id.
* ``oauth``: an OAuth 2.1 access token this service issued (app/oauth.py): a client acting
  for a signed-in person, within the token's scopes (``tools:read``, ``tools:write``,
  ``admin``; the last two only for people on the administrator list when it is set).
* ``machine``: a client-credentials token: a machine client bound to an app, acting as that app
  within the scopes it was registered with (like a key, but expiring). Recorded as ``client:<id>``.
* ``anonymous``: nothing presented. Allowed for read-tier tools only while
  ``MCP_REQUIRE_KEYS`` is not ``1`` and the request did not come in by the public path;
  never for write-tier tools.

The identity header ``X-Auth-Request-Email`` is trusted only when the request also carries
``X-Mcp-Proxy-Secret`` equal to ``MCP_PROXY_SECRET``: that secret is set in the proxy's
route (proxy_server/conf/secrets/mcp-console.conf) and nowhere else, so a caller on the
internal network cannot name a person. Without the secret configured, the header is ignored.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from app import keys, oauth

IDENTITY_HEADER = "x-auth-request-email"
SECRET_HEADER = "x-mcp-proxy-secret"


class AuthError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


@dataclass
class Caller:
    kind: str                 # admin | person | key | anonymous
    label: str                # console | <email> | <key id> | anonymous
    app: str | None = None    # the key's app
    key: dict | None = None
    email: str | None = None  # the signed-in person, when the proxy named one, or the OAuth token's subject
    via: str = "none"         # token | proxy | key | oauth | none
    scopes: tuple = ()        # an OAuth token's scopes


ANONYMOUS = Caller("anonymous", "anonymous")


def admin_token() -> str:
    return os.getenv("MCP_ADMIN_TOKEN", "")


def proxy_secret() -> str:
    return os.getenv("MCP_PROXY_SECRET", "").strip()


def admin_emails() -> set[str]:
    return {e.strip().lower() for e in os.getenv("MCP_ADMIN_EMAILS", "").split(",") if e.strip()}


def require_keys() -> bool:
    return os.getenv("MCP_REQUIRE_KEYS", "0") == "1"


def mode() -> str:
    """For /health and the console header."""
    return "required" if require_keys() else "optional"


def bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def person_from(headers: Mapping[str, str]) -> str | None:
    """The signed-in person, only when the proxy secret proves the header came through
    the proxy (never from a caller that set it itself)."""
    secret = proxy_secret()
    if not secret or headers.get(SECRET_HEADER) != secret:
        return None
    email = (headers.get(IDENTITY_HEADER) or "").strip().lower()
    return email or None


def resolve(headers: Mapping[str, str]) -> Caller:
    """The caller behind a request's headers (lower-case keys, as FastAPI and ASGI give them)."""
    token = bearer(headers.get("authorization"))
    if token:
        if admin_token() and token == admin_token():
            return Caller("admin", "console", via="token")
        if oauth.looks_like_jwt(token):
            claims = oauth.verify_access_token(token)
            if not claims:
                raise AuthError(401, "the access token is invalid or expired")
            if claims.get("app"):          # a machine client's token: it speaks for its app, nobody behind it
                return Caller("machine", f"client:{claims['client_id']}", app=str(claims["app"]), via="oauth",
                              scopes=tuple(str(claims["scope"]).split()))
            sub = str(claims["sub"]).lower()
            return Caller("oauth", f"oauth:{sub}", email=sub, via="oauth", scopes=tuple(str(claims["scope"]).split()))
        rec = keys.verify(token)
        if rec:
            return Caller("key", rec["id"], app=rec["app"], key=rec, via="key")
        raise AuthError(401, "the key presented is unknown, revoked or expired")
    email = person_from(headers)
    if email:
        allowed = admin_emails()
        if not allowed or email in allowed:
            return Caller("admin", email, email=email, via="proxy")
        return Caller("person", email, email=email, via="proxy")
    return ANONYMOUS


def is_admin(headers: Mapping[str, str]) -> bool:
    """Admin writes: open when neither an admin token nor a proxy secret is configured (dev)."""
    if not admin_token() and not proxy_secret():
        return True
    try:
        c = resolve(headers)
    except AuthError:
        return False
    return c.kind == "admin" or (c.kind == "oauth" and "admin" in c.scopes and _listed(c.email))


def _listed(email: str | None) -> bool:
    allowed = admin_emails()
    return not allowed or (email or "") in allowed


def is_public(headers: Mapping[str, str]) -> bool:
    """The request came in by the public path (the proxy marks it): nobody is anonymous there."""
    return headers.get("x-mcp-public") == "1"


def require_admin(headers: Mapping[str, str]) -> None:
    if not is_admin(headers):
        raise AuthError(401, "admin bearer token required, or sign in through the domain proxy as an administrator")


def enforce(tool: dict, app: str | None, caller: Caller) -> None:
    """May this caller invoke this tool for this app?"""
    if caller.kind in ("key", "machine") and app and caller.app != app:
        raise AuthError(403, f"this {'key' if caller.kind == 'key' else 'client'} belongs to app '{caller.app}', not '{app}'")
    if caller.kind in ("admin", "key"):
        return
    if caller.kind == "machine":
        if tool.get("tier") == "write" and "tools:write" not in caller.scopes:
            raise AuthError(403, "a write-tier tool needs the tools:write scope")
        return
    if caller.kind == "oauth":
        if tool.get("tier") == "write":
            if "tools:write" not in caller.scopes:
                raise AuthError(403, "a write-tier tool needs the tools:write scope")
            if not _listed(caller.email):
                raise AuthError(403, "write-tier tools over OAuth are for administrators")
            return
        if not ({"tools:read", "tools:write", "admin"} & set(caller.scopes)):
            raise AuthError(403, "the token has no tools scope")
        return
    # anonymous, or a signed-in person who is not an administrator
    if tool.get("tier") == "write":
        raise AuthError(401, "a write-tier tool needs an app key (Authorization: Bearer mcpk_…) or an administrator")
    if require_keys() and caller.kind == "anonymous":
        raise AuthError(401, "an app key is required (Authorization: Bearer mcpk_…)")
