"""End to end over the standard MCP endpoint: initialize, tools/list with annotations,
tools/call (validated, authorised, recorded, structured), prompts and resources."""
from __future__ import annotations

from conftest import ECHO_TOOL, WRITE_TOOL, mcp_call


def _setup(service):
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    service.put("/tools/wecho", json=WRITE_TOOL, headers=service.admin)
    service.put("/skills/cite_with_tag", json={"apps": ["testapp", "tutor", "slides"]}, headers=service.admin)
    return service.post("/apps/testapp/keys", json={"name": "k"}, headers=service.admin).json()["key"]


def test_initialize_and_tools_list(service):
    _setup(service)
    r = mcp_call(service, "testapp", "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                                   "clientInfo": {"name": "t", "version": "0"}})
    assert r.status_code == 200, r.text
    res = r.json()["result"]
    assert res["serverInfo"]["name"] == "mcp-service"
    assert {"tools", "prompts", "resources", "experimental"} <= set(res["capabilities"])
    assert res["capabilities"]["experimental"]["registry"]["version"] == "2"
    tools = {t["name"]: t for t in mcp_call(service, "testapp", "tools/list").json()["result"]["tools"]}
    assert set(tools) == {"echo", "wecho"}          # scoped: the seeds belong to other apps
    assert tools["echo"]["annotations"]["readOnlyHint"] is True
    assert tools["wecho"]["annotations"] == {"title": "Write echo", "readOnlyHint": False, "destructiveHint": True,
                                             "idempotentHint": False, "openWorldHint": None} or \
           (tools["wecho"]["annotations"]["destructiveHint"] is True and tools["wecho"]["annotations"]["readOnlyHint"] is False)
    assert tools["wecho"]["outputSchema"]["required"] == ["echo"]
    assert "web_search" in {t["name"] for t in mcp_call(service, "job2cool", "tools/list").json()["result"]["tools"]}


def test_tools_call_paths(service):
    key = _setup(service)
    # read tier, anonymous allowed (keys optional): validated and recorded
    r = mcp_call(service, "testapp", "tools/call", {"name": "echo", "arguments": {"n": 1}})
    res = r.json()["result"]
    assert res["isError"] is True and "invalid_arguments" in res["content"][0]["text"]
    r = mcp_call(service, "testapp", "tools/call", {"name": "echo", "arguments": {"text": "hi"}},
                 headers={"X-On-Behalf-Of": "ana@example.com"})
    res = r.json()["result"]
    assert res["isError"] is False and '"text": "hi"' in res["content"][0]["text"]
    rec = service.get("/activity?tool=echo&window=1h&ok=true").json()["calls"][0]
    assert rec["transport"] == "mcp" and rec["on_behalf_of"] == "ana@example.com" and rec["caller"] == "anonymous"
    # write tier: refused without a key, structured with one
    res = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}}).json()["result"]
    assert res["isError"] is True and "unauthorized" in res["content"][0]["text"]
    r = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}},
                 headers={"Authorization": f"Bearer {key}"})
    res = r.json()["result"]
    assert res["isError"] is False and res["structuredContent"]["echo"] == {"text": "x"}
    # a key for another app is refused at the door
    r = mcp_call(service, "job2cool", "tools/list", headers={"Authorization": f"Bearer {key}"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
    # unknown tool in this scope
    res = mcp_call(service, "testapp", "tools/call", {"name": "web_search", "arguments": {"query": "q"}}).json()["result"]
    assert res["isError"] is True and "unknown or disabled" in res["content"][0]["text"]


def test_require_keys_rejects_anonymous_mcp(service, monkeypatch):
    key = _setup(service)
    monkeypatch.setenv("MCP_REQUIRE_KEYS", "1")
    r = mcp_call(service, "testapp", "tools/list")
    assert r.status_code == 401
    assert mcp_call(service, "testapp", "tools/list", headers={"Authorization": f"Bearer {key}"}).status_code == 200


def test_prompts_and_resources(service):
    _setup(service)
    prompts = {p["name"]: p for p in mcp_call(service, "testapp", "prompts/list").json()["result"]["prompts"]}
    assert set(prompts) == {"cite_with_tag"}
    assert prompts["cite_with_tag"]["arguments"][0]["name"] == "kb_tool"
    r = mcp_call(service, "testapp", "prompts/get", {"name": "cite_with_tag", "arguments": {"kb_tool": "kb_search"}})
    text = r.json()["result"]["messages"][0]["content"]["text"]
    assert "returned by kb_search" in text
    res = mcp_call(service, "testapp", "resources/list").json()["result"]["resources"]
    assert res[0]["uri"] == "skill://cite_with_tag" and res[0]["mimeType"] == "text/markdown"
    r = mcp_call(service, "testapp", "resources/read", {"uri": "skill://cite_with_tag"})
    assert "{{kb_tool}}" in r.json()["result"]["contents"][0]["text"]
    # disabled skills disappear from every face
    service.patch("/skills/cite_with_tag/enabled", json={"enabled": False}, headers=service.admin)
    assert mcp_call(service, "testapp", "prompts/list").json()["result"]["prompts"] == []
    assert mcp_call(service, "testapp", "resources/list").json()["result"]["resources"] == []
