"""Mount the MCP Streamable-HTTP transport at /mcp/ (reuses noted's pattern).

Per request: the app comes from the path (``/mcp/{app}/``), the caller from the
``Authorization`` header (admin token or app key) or from the domain proxy's signed-in
person (``X-Auth-Request-Email`` with the proxy secret), the person acted for from
``X-On-Behalf-Of`` (or the signed-in person themselves).
A key for another app, or no key where one is required, is refused here, before the
session manager sees the request.
"""
from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from starlette.routing import Mount

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from app import auth, oauth, registry
from app.mcpserver import current_app, current_caller, current_obo

logger = logging.getLogger("mcp-service.mount")


async def _reject(send, status: int, detail: str) -> None:
    body = json.dumps({"error": {"code": "unauthorized" if status == 401 else "forbidden",
                                 "message": detail}}).encode()
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    if status == 401:
        # the MCP specification: a 401 names the protected-resource metadata, where the OAuth flow starts
        headers.append((b"www-authenticate", oauth.www_authenticate("invalid_token" if "token" in detail else None, detail).encode()))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def mount_mcp(app: FastAPI, server: Server) -> StreamableHTTPSessionManager:
    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,
        stateless=True,
    )

    async def mcp_asgi_app(scope, receive, send):
        # Mount strips the "/mcp" prefix, so scope["path"] is "/{app}" (or "/"
        # for the un-scoped aggregate endpoint). Pin the app for this request
        # so the server's list/call handlers filter to it, then normalise the
        # path to root for the (path-agnostic, stateless) session manager.
        raw = scope.get("path", "") or "/"
        segs = [p for p in raw.split("/") if p]
        if segs and segs[0] == "mcp":
            segs = segs[1:]
        app_name = segs[0] if segs else None

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}
        try:
            caller = auth.resolve(headers)
        except auth.AuthError as e:
            await _reject(send, e.status, e.detail)
            return
        if caller.kind in ("key", "machine") and app_name and caller.app != app_name:
            await _reject(send, 403, f"this {'key' if caller.kind == 'key' else 'client'} belongs to app '{caller.app}', not '{app_name}'")
            return
        if app_name and (registry.get_app(app_name) or {}).get("status") == "retired":
            await _reject(send, 403, f"app '{app_name}' is retired")
            return
        if caller.kind == "anonymous" and (auth.require_keys() or auth.is_public(headers)):
            await _reject(send, 401, "sign in with OAuth, or present an app key (Authorization: Bearer …)")
            return

        tokens = (current_app.set(app_name), current_caller.set(caller),
                  current_obo.set(headers.get("x-on-behalf-of") or caller.email))
        scope = dict(scope)
        scope["path"] = "/"
        scope["raw_path"] = b"/"
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            current_app.reset(tokens[0])
            current_caller.reset(tokens[1])
            current_obo.reset(tokens[2])

    app.router.routes.append(Mount("/mcp", app=mcp_asgi_app))
    logger.info("MCP server mounted at /mcp (Streamable HTTP, per-app /mcp/{app}/)")
    return session_manager
