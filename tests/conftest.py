"""Every test runs against a fresh data directory and a stub implementation, with the
admin token set, so the auth paths are exercised the way production runs them."""
from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MCP_ADMIN_TOKEN", "admin-secret")
    monkeypatch.delenv("MCP_REQUIRE_KEYS", raising=False)
    monkeypatch.delenv("MCP_RECORD_ARGS", raising=False)

    from app import toolimpl

    async def echo(args, config):
        return {"echo": args, "config": config}

    async def boom(args, config):
        raise RuntimeError("backend exploded")

    toolimpl.IMPLS["echo"] = echo
    toolimpl.IMPLS["boom"] = boom

    import app.main as main
    importlib.reload(main)
    from fastapi.testclient import TestClient

    with TestClient(main.app) as client:
        client.admin = {"Authorization": "Bearer admin-secret"}
        # the application catalog: offers and keys need a registered app
        for name in ("testapp", "other"):
            assert client.put(f"/apps/{name}", json={"display_name": name, "owner": "tests"}, headers=client.admin).status_code == 200
        yield client
    toolimpl.IMPLS.pop("echo", None)
    toolimpl.IMPLS.pop("boom", None)


ECHO_TOOL = {
    "display_name": "Echo", "description": "returns its arguments", "impl": "echo", "tier": "read",
    "apps": ["testapp"],
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"},
                                                       "n": {"type": "integer", "minimum": 1}},
                     "required": ["text"]},
}

WRITE_TOOL = {
    "display_name": "Write echo", "description": "a write-tier echo", "impl": "echo", "tier": "write",
    "destructive": True, "apps": ["testapp"],
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    "output_schema": {"type": "object", "properties": {"echo": {"type": "object"}}, "required": ["echo"]},
}


def mcp_call(client, app, method, params=None, headers=None, id_=1):
    h = {"content-type": "application/json", "accept": "application/json, text/event-stream"}
    h.update(headers or {})
    body = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        body["params"] = params
    return client.post(f"/mcp/{app}/", json=body, headers=h)
