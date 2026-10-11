"""The application catalog: records, registration before offers and keys, retirement, deletion, history."""
from __future__ import annotations

from conftest import ECHO_TOOL, mcp_call


def test_seed_registers_the_apps_records_name(service):
    # the seeds' apps were registered on first load, with the note that says so
    apps = {a["name"]: a for a in service.get("/apps").json()["apps"]}
    assert apps["job2cool"]["registered"] and apps["factory"]["registered"] and apps["tutor"]["registered"]
    assert apps["job2cool"]["status"] == "active" and apps["job2cool"]["tools"] == 1
    rec = service.get("/apps/job2cool").json()
    assert rec["version"] == 1 and "automatically" in rec["description"]


def test_offers_and_keys_need_a_registered_app(service):
    tool = {**ECHO_TOOL, "apps": ["newapp"]}
    r = service.put("/tools/echo", json=tool, headers=service.admin)       # newapp is not registered
    assert r.status_code == 422 and "unknown app(s): newapp" in r.json()["detail"]
    assert service.post("/apps/newapp/keys", json={"name": "k"}, headers=service.admin).status_code == 422
    r = service.put("/apps/newapp", json={"display_name": "New app", "owner": "QA", "contact": "qa@example.com",
                                          "description": "for the tests", "tags": ["test"]}, headers=service.admin)
    assert r.status_code == 200 and r.json()["version"] == 1 and r.json()["status"] == "active"
    assert service.put("/apps/bad name", json={}, headers=service.admin).status_code == 422
    assert service.put("/apps/newapp", json={"status": "gone"}, headers=service.admin).status_code == 422
    assert service.put("/apps/newapp", json={}).status_code == 401
    assert service.put("/tools/echo", json=tool, headers=service.admin).status_code == 200
    assert service.post("/apps/newapp/keys", json={"name": "k"}, headers=service.admin).status_code == 201
    view = service.get("/apps/newapp").json()
    assert view["tools"] == 1 and len(view["keys"]) == 1 and view["owner"] == "QA" and view["registered"]


def test_retired_app_is_refused_everywhere(service):
    service.put("/apps/testapp", json={}, headers=service.admin)
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    key = service.post("/apps/testapp/keys", json={"name": "k"}, headers=service.admin).json()["key"]
    service.put("/apps/testapp", json={"status": "retired"}, headers=service.admin)
    assert service.post("/apps/testapp/keys", json={"name": "k2"}, headers=service.admin).status_code == 422
    r = service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"})
    assert r.status_code == 403 and "retired" in r.json()["detail"]
    r = mcp_call(service, "testapp", "tools/list", headers={"Authorization": f"Bearer {key}"})
    assert r.status_code == 403
    att = service.get("/admin/attention").json()["items"]
    assert any("Retired app" in i["title"] for i in att)
    service.put("/apps/testapp", json={"status": "active"}, headers=service.admin)
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"Authorization": f"Bearer {key}"}).status_code == 200


def test_delete_app_rules_and_history(service):
    service.put("/apps/testapp", json={"owner": "A"}, headers=service.admin)
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    kid = service.post("/apps/testapp/keys", json={"name": "k"}, headers=service.admin).json()["record"]["id"]
    # in use: refused without force
    r = service.delete("/apps/testapp", headers=service.admin)
    assert r.status_code == 409
    service.delete(f"/apps/testapp/keys/{kid}", headers=service.admin)
    r = service.delete("/apps/testapp", headers=service.admin)
    assert r.status_code == 409 and "offered" in r.json()["detail"]
    # force: the app is withdrawn from its tools, which are then offered to nobody (flagged)
    assert service.delete("/apps/testapp?force=true", headers=service.admin).json()["deleted"] is True
    assert service.get("/tools/echo").json()["apps"] == []
    assert any("offered to no app" in i["title"] for i in service.get("/admin/attention").json()["items"])
    h = service.get("/apps/testapp/history").json()["history"]
    assert [e["action"] for e in h] == ["create", "update", "delete"]
    assert service.post("/apps/testapp/restore", json={"version": 2}, headers=service.admin).json()["owner"] == "A"
    assert service.get("/apps/testapp").json()["registered"]
