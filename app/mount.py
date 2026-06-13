"""Mount the MCP Streamable-HTTP transport at /mcp/ (reuses noted's pattern).

The returned session manager MUST be run inside the FastAPI lifespan:
    async with session_manager.run():
        yield
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from starlette.routing import Mount

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from app.mcpserver import current_app

logger = logging.getLogger("mcp-service.mount")


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
        app_name = segs[0] if segs else None
        token = current_app.set(app_name)
        scope = dict(scope)
        scope["path"] = "/"
        scope["raw_path"] = b"/"
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            current_app.reset(token)

    app.router.routes.append(Mount("/mcp", app=mcp_asgi_app))
    logger.info("MCP server mounted at /mcp (Streamable HTTP, per-app /mcp/{app}/)")
    return session_manager
