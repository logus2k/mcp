from __future__ import annotations

from conftest import ECHO_TOOL, WRITE_TOOL


def _setup(service):
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    service.put("/tools/wecho", json=WRITE_TOOL, headers=service.admin)
    r = service.post("/apps/testapp/keys", json={"name": "test program", "expires_days": 30}, headers=service.admin)
    assert r.status_code == 201
    key = r.json()["key"]
    assert key.startswith("mcpk_") and len(key) == 5 + 43
    return key


def test_invoke_validates_runs_and_records(service):
    _setup(service)
    r = service.post("/tools/echo/invoke", json={"args": {"n": 0}})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_arguments" and r.json()["error"]["path"] == "/"   # missing 'text'
    r = service.post("/tools/echo/invoke", json={"args": {"text": "hi", "n": 0}})
    assert r.status_code == 422 and r.json()["error"]["path"] == "/n"
    r = service.post("/tools/echo/invoke", json={"args": {"text": "hi", "n": 2}}, headers={"X-On-Behalf-Of": "ana@example.com"})
    assert r.status_code == 200 and r.json()["result"]["echo"] == {"text": "hi", "n": 2} and r.json()["app"] == "testapp"
    calls = service.get("/activity?tool=echo&window=1h").json()["calls"]
    assert len(calls) == 3
    ok = [c for c in calls if c["ok"]][0]
    assert ok["caller"] == "anonymous" and ok["on_behalf_of"] == "ana@example.com" and ok["transport"] == "rest"
    assert ok["args_json"] is None and len(ok["args_digest"]) == 64
    bad = [c for c in calls if not c["ok"]]
    assert all("invalid_arguments" in c["error"] for c in bad)
    s = service.get("/activity/summary?window=1h").json()
    assert s["calls"] == 3 and s["errors"] == 2 and s["tools"][0]["tool"] == "echo" and "echo" in s["last_used"]
    csv = service.get("/activity.csv?window=1h").text
    assert csv.splitlines()[0].startswith("ts,app,tool") and len(csv.splitlines()) == 4


def test_write_tier_needs_a_key_and_key_binds_to_app(service):
    key = _setup(service)
    r = service.post("/tools/wecho/invoke", json={"args": {"text": "x"}})
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"
    r = service.post("/tools/wecho/invoke", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"})
    assert r.status_code == 200
    rec = service.get("/activity?tool=wecho&window=1h").json()["calls"][0]
    assert rec["caller"] == service.get("/apps/testapp/keys").json()["keys"][0]["id"]
    # the key is for testapp; offering the tool to another app and calling for that app is refused
    service.put("/tools/wecho?app=other", json={}, headers=service.admin)
    r = service.post("/tools/wecho/invoke?app=other", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"})
    assert r.status_code == 403
    # the admin token may run anything and is recorded as the console
    r = service.post("/tools/wecho/invoke?app=other", json={"args": {"text": "x"}}, headers=service.admin)
    assert r.status_code == 200
    assert service.get("/activity?tool=wecho&app=other&window=1h").json()["calls"][0]["caller"] == "console"
    # an unknown key is refused outright
    r = service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"Authorization": "Bearer mcpk_nope"})
    assert r.status_code == 401


def test_require_keys_flag_and_revocation(service, monkeypatch):
    key = _setup(service)
    monkeypatch.setenv("MCP_REQUIRE_KEYS", "1")
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}).status_code == 401
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"}).status_code == 200
    kid = service.get("/apps/testapp/keys").json()["keys"][0]["id"]
    assert service.delete(f"/apps/testapp/keys/{kid}", headers=service.admin).json()["revoked"] is True
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"}).status_code == 401
    listed = service.get("/apps/testapp/keys").json()["keys"][0]
    assert listed["revoked_at"] and "fingerprint" not in listed
    apps = {a["name"]: a for a in service.get("/apps").json()["apps"]}
    assert apps["testapp"]["tools"] == 2 and apps["testapp"]["keys"] == []


def test_tool_failure_is_502_and_recorded(service):
    service.put("/tools/kaboom", json={**ECHO_TOOL, "impl": "boom"}, headers=service.admin)
    r = service.post("/tools/kaboom/invoke", json={"args": {"text": "x"}})
    assert r.status_code == 502 and "backend exploded" in r.json()["error"]["message"]
    assert service.get("/activity?tool=kaboom&window=1h").json()["calls"][0]["error"].startswith("RuntimeError")


def test_console_endpoints(service):
    _setup(service)
    service.post("/tools/echo/invoke", json={"args": {"text": "x"}})
    reg = service.get("/admin/registry").json()
    echo = [t for t in reg["tools"] if t["name"] == "echo"][0]
    assert echo["calls_24h"] == 1 and echo["last_used"] and "echo" in reg["impl_tools"]
    assert reg["keys"][0]["app"] == "testapp" and "fingerprint" not in reg["keys"][0]
    att = service.get("/admin/attention").json()["items"]
    assert any("optional" in i["title"] for i in att)       # keys not required in this run
    assert any("Anonymous" in i["title"] for i in att)
    page = service.get("/admin")
    assert page.status_code == 200 and "<title>MCP Server</title>" in page.text
    h = service.get("/health").json()
    assert h["app_keys"] == "optional" and "apps" in h


def test_help_and_docs_are_served(service):
    toc = service.get("/admin/help/manual/README.md")
    assert toc.status_code == 200 and toc.text.startswith("# MCP Server User Manual")
    assert service.get("/admin/help/guide/01-overview.md").status_code == 200
    assert service.get("/admin/help/manual/../../main.py").status_code in (404, 400)
    assert service.get("/admin/help/other/README.md").status_code == 404
    assert service.get("/admin/docs/architecture").text.startswith("# mcp-service")
    assert service.get("/admin/docs/nope").status_code == 404
    assert service.get("/admin/vendor/marked.min.js").status_code == 200
    assert service.get("/admin/vendor/evil.js").status_code == 404


def test_portuguese_manual_and_dictionary(service):
    toc = service.get("/admin/help/manual/pt/README.md")
    assert toc.status_code == 200 and toc.text.startswith("# Manual do utilizador do MCP Server")
    en = service.get("/admin/help/manual/README.md").text
    import os
    pages = [l[l.index("](") + 2:l.index(")", l.index("]("))] for l in en.splitlines() if l.startswith("- [")]
    for p in pages:
        assert service.get(f"/admin/help/manual/pt/{p}").status_code == 200, p
    d = service.get("/admin/i18n/pt.js")
    assert d.status_code == 200 and "window.MCP_PT" in d.text and '"Tools": "Ferramentas"' in d.text
    assert service.get("/admin/i18n/en.js").status_code == 404
