"""The signed-in person's profile, as Cortex does it (cortex/server/identity.py): the proxy
forwards Microsoft Graph's access token (``X-Access-Token``) only so the page can show the
person's own name and photo, and the ID token (``X-Id-Token``) only as the sign-out hint.

* ``MCP_USERINFO_URL``  the OpenID Connect UserInfo endpoint (default: Microsoft Graph's)
* ``MCP_PHOTO_URL``     where the photo is read with the same token (default: Graph, 96x96);
                        downloaded here and handed to the page as data, never as that address
* ``MCP_SIGN_OUT_URL``  where Sign out goes; ``{logout_hint}`` is filled from the ID token so
                        Entra ID ends the session without asking which account
* ``MCP_IDENTITY_PROFILE=0`` skips the lookup (the name is then the start of the address)
Everything degrades: no token or a failed lookup still shows the address and initials.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from urllib.parse import quote

import httpx

log = logging.getLogger("mcp-service.identity")

_DEFAULT_SIGN_OUT = ("/oauth2-entra/sign_out?rd=https%3A%2F%2Flogin.microsoftonline.com%2Fcommon%2Foauth2%2Fv2.0%2Flogout"
                     "%3Fpost_logout_redirect_uri%3Dhttps%253A%252F%252Flogus2k.com%252Fmcp-console%252Fadmin{logout_hint}")
_cache: dict[str, tuple[float, dict]] = {}


def userinfo_url() -> str:
    return os.getenv("MCP_USERINFO_URL", "").strip() or "https://graph.microsoft.com/oidc/userinfo"


def photo_url() -> str:
    return os.getenv("MCP_PHOTO_URL", "https://graph.microsoft.com/v1.0/me/photos/96x96/$value").strip()


def profile_enabled() -> bool:
    return os.getenv("MCP_IDENTITY_PROFILE", "1") not in ("0", "false", "no")


def sign_out_url(id_token: str | None) -> str:
    """``MCP_SIGN_OUT_URL`` with ``{logout_hint}`` filled from the ID token's ``login_hint`` claim,
    encoded twice (a value inside the provider's address, itself a value of the proxy's ``rd=``)."""
    template = os.getenv("MCP_SIGN_OUT_URL", "").strip() or _DEFAULT_SIGN_OUT
    token = (id_token or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    ok = bool(token) and all(c.isalnum() or c in "-_." for c in token) and token.count(".") == 2
    hint = ""
    if ok:
        try:
            body = token.split(".")[1]
            hint = str(json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))).get("login_hint") or "")
        except (ValueError, UnicodeDecodeError):
            hint = ""
    twice = quote(quote(hint, safe=""), safe="")
    return template.replace("{logout_hint}", f"%26logout_hint%3D{twice}" if hint else "")


async def profile(token: str | None) -> dict:
    """``{name, picture}`` for the access token; cached 15 minutes; failures give ``{}``."""
    token = (token or "").strip()
    if not token or not profile_enabled():
        return {}
    now = time.time()
    hit = _cache.get(token)
    if hit and hit[0] > now:
        return hit[1]
    info: dict = {}
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(userinfo_url(), headers={"Authorization": f"Bearer {token}"})
            if r.status_code >= 400:
                log.warning("identity: userinfo (%s) answered HTTP %s: %s", userinfo_url(), r.status_code, r.text[:200])
            else:
                body = r.json()
                info = {"name": body.get("name") or body.get("preferred_username") or "", "picture": body.get("picture")}
                if photo_url():
                    info["picture"] = None
                    ph = await c.get(photo_url(), headers={"Authorization": f"Bearer {token}"})
                    kind = ph.headers.get("content-type", "").split(";")[0].strip()
                    if ph.status_code == 200 and kind.startswith("image/") and len(ph.content) <= 200_000:
                        info["picture"] = f"data:{kind};base64,{base64.b64encode(ph.content).decode()}"
                    else:
                        log.info("identity: no photo (HTTP %s, %s)", ph.status_code, kind or "no type")
    except Exception as ex:  # noqa: BLE001 — decoration, never fatal
        log.warning("identity: userinfo (%s) failed: %s", userinfo_url(), ex)
        info = {}
    if len(_cache) > 256:
        _cache.clear()
    _cache[token] = (now + 900, info)
    return info
