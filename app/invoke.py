"""One invocation pipeline for both faces: authorise, validate, run, record.

REST ``POST /tools/{name}/invoke`` and MCP ``tools/call`` both go through ``run`` so a
call is treated the same way and recorded the same way whichever door it came in by.
"""
from __future__ import annotations

import json
import logging
import time

from app import activity, auth, toolimpl, validation

logger = logging.getLogger("mcp-service.invoke")


class InvokeError(Exception):
    def __init__(self, status: int, error: dict):
        super().__init__(error.get("message", "invoke failed"))
        self.status = status
        self.error = error


def _record(tool: dict, app: str | None, caller: auth.Caller, obo: str | None, transport: str,
            args: dict | None, started: float, ok: bool, error: str | None, result=None) -> None:
    text = result if isinstance(result, str) else (json.dumps(result, ensure_ascii=False) if result is not None else "")
    try:
        activity.record(app=app, tool=tool["name"], transport=transport, caller=caller.label, on_behalf_of=obo,
                        ok=ok, error=error, duration_ms=int((time.monotonic() - started) * 1000),
                        args=args, tier=tool.get("tier", "read"), result_chars=len(text) if ok else None)
    except Exception:  # noqa: BLE001 — the record must never take the call down with it
        logger.exception("could not record the call")


async def run(tool: dict, app: str | None, args: dict | None, caller: auth.Caller, obo: str | None,
              transport: str):
    """The tool's result, or ``InvokeError`` with the status and error the caller receives."""
    started = time.monotonic()
    args = args or {}
    try:
        auth.enforce(tool, app, caller)
    except auth.AuthError as e:
        _record(tool, app, caller, obo, transport, args, started, False, f"{e.status}: {e.detail}")
        raise InvokeError(e.status, {"code": "unauthorized" if e.status == 401 else "forbidden",
                                     "message": e.detail}) from e
    if not tool.get("enabled", True):
        _record(tool, app, caller, obo, transport, args, started, False, "409: tool disabled")
        raise InvokeError(409, {"code": "disabled", "message": "tool disabled"})
    if (tool.get("config") or {}).get("execution", "server") == "client":
        _record(tool, app, caller, obo, transport, args, started, False, "409: client-executed tool")
        raise InvokeError(409, {"code": "client_executed",
                                "message": "this tool is executed by the app's own page, not by the service"})
    err = validation.validate(tool.get("input_schema"), args)
    if err:
        _record(tool, app, caller, obo, transport, args, started, False, f"{err['code']} at {err['path']}: {err['message']}")
        raise InvokeError(422, err)
    try:
        result = await toolimpl.invoke(tool["impl"], args, tool.get("config") or {})
    except Exception as e:  # noqa: BLE001
        logger.exception("invoke failed")
        message = f"{type(e).__name__}: {e}"
        _record(tool, app, caller, obo, transport, args, started, False, message)
        raise InvokeError(502, {"code": "tool_failed", "message": message}) from e
    _record(tool, app, caller, obo, transport, args, started, True, None, result)
    return result
