from __future__ import annotations

import json
import os

from conftest import ECHO_TOOL


def test_seed_and_round_trip(service):
    names = {t["name"] for t in service.get("/tools").json()["tools"]}
    assert {"web_search", "nginx_register_app"} <= names
    skills = {s["name"] for s in service.get("/skills").json()["skills"]}
    assert {"cite_with_tag", "pt_pt_style", "ai_generated_disclosure"} == skills

    r = service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    assert r.status_code == 200, r.text
    rec = r.json()
    assert rec["apps"] == ["testapp"] and rec["version"] == 1
    assert service.get("/tools/echo").json()["impl"] == "echo"
    assert [t["name"] for t in service.get("/tools?app=testapp").json()["tools"]] == ["echo"]
    assert service.get("/tools/manifest?app=testapp").json()["tools"][0]["input_schema"]["required"] == ["text"]


def test_writes_need_admin_token(service):
    assert service.put("/tools/echo", json=ECHO_TOOL).status_code == 401
    assert service.put("/tools/echo", json=ECHO_TOOL, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert service.delete("/tools/web_search").status_code == 401


def test_put_rejects_unknown_impl_and_bad_schema(service):
    r = service.put("/tools/x", json={**ECHO_TOOL, "impl": "nope"}, headers=service.admin)
    assert r.status_code == 422 and "unknown impl" in r.text
    r = service.put("/tools/x", json={**ECHO_TOOL, "input_schema": {"type": "not-a-type"}}, headers=service.admin)
    assert r.status_code == 422 and "JSON Schema" in r.text


def test_app_scoped_put_adds_app_and_delete_withdraws(service):
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    r = service.put("/tools/echo?app=other", json={"description": "shared"}, headers=service.admin)
    assert r.json()["apps"] == ["other", "testapp"] and r.json()["version"] == 2
    assert service.delete("/tools/echo?app=other", headers=service.admin).json()["deleted"] is True
    assert service.get("/tools/echo").json()["apps"] == ["testapp"]
    assert service.delete("/tools/echo", headers=service.admin).json()["deleted"] is True
    assert service.get("/tools/echo").status_code == 404


def test_history_and_restore(service):
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    service.put("/tools/echo", json={"description": "second"}, headers=service.admin)
    h = service.get("/tools/echo/history").json()["history"]
    assert [e["version"] for e in h] == [1, 2] and h[-1]["actor"] == "console"
    r = service.post("/tools/echo/restore", json={"version": 1}, headers=service.admin)
    assert r.status_code == 200 and r.json()["description"] == "returns its arguments" and r.json()["version"] == 3
    assert service.post("/tools/echo/restore", json={"version": 9}, headers=service.admin).status_code == 404


def test_migration_from_v1(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_DATA_DIR", str(tmp_path))
    v1 = {"tools": {
        "a/web_search": {"name": "web_search", "app": "a", "impl": "web_search", "tier": "read",
                         "input_schema": {"type": "object"}, "config": {}, "created_at": "2026-01-01"},
        "b/web_search": {"name": "web_search", "app": "b", "impl": "web_search", "tier": "read",
                         "input_schema": {"type": "object"}, "config": {"execution": "server"}, "created_at": "2026-01-02"},
        "a/fetch": {"name": "fetch", "app": "a", "impl": "fetch_url", "tier": "read",
                    "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}}, "config": {}, "created_at": "2026-01-01"},
        "c/fetch": {"name": "fetch", "app": "c", "impl": "fetch_url", "tier": "read",
                    "input_schema": {"type": "object"}, "config": {}, "created_at": "2026-01-03"},
    }, "skills": {"a/s": {"name": "s", "app": "a", "content": "x", "triggers": ["t"], "priority": 5}}}
    (tmp_path / "registry.json").write_text(json.dumps(v1))
    from app import registry
    tools = {t["name"]: t for t in registry.list_tools()}
    assert tools["web_search"]["apps"] == ["a", "b"]           # identical: merged
    assert tools["fetch"]["apps"] == ["a"]                      # differs: first keeps the name
    assert tools["fetch__c"]["apps"] == ["c"]                   # the other is renamed
    s = registry.get_skill("s")
    assert s["apps"] == ["a"] and "triggers" not in s and "priority" not in s
    report = json.loads((tmp_path / "migration_report.json").read_text())
    assert [m["name"] for m in report["merged"]] == ["web_search"]
    assert report["renamed"][0]["to"] == "fetch__c"
    assert json.loads((tmp_path / "registry.json").read_text())["version"] == 2


def test_skill_render_and_crud(service):
    r = service.post("/skills/cite_with_tag/render", json={"arguments": {"kb_tool": "kb_search"}})
    assert "returned by kb_search" in r.json()["messages"][0]["content"]
    r = service.post("/skills/cite_with_tag/render", json={})
    assert "{{kb_tool}}" in r.json()["messages"][0]["content"]   # optional, unresolved as written
    r = service.put("/skills/greet", json={"content": "Hello {{who}}", "apps": ["testapp"],
                                           "arguments": [{"name": "who", "required": True}]}, headers=service.admin)
    assert r.status_code == 200 and r.json()["version"] == 1
    assert service.post("/skills/greet/render", json={}).status_code == 422
    assert service.post("/skills/greet/render", json={"arguments": {"who": "Ana"}}).json()["messages"][0]["content"] == "Hello Ana"
