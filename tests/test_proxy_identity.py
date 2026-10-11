"""The domain proxy's signed-in person (Microsoft Entra ID through oauth2-proxy-entra):
trusted only with the proxy secret, an administrator without any pasted token."""
from __future__ import annotations

from conftest import ECHO_TOOL, WRITE_TOOL, mcp_call

PROXY = {"X-Mcp-Proxy-Secret": "proxy-secret", "X-Auth-Request-Email": "Antonio.S.Cruz@bancoctt.pt"}


def test_identity_header_is_ignored_without_the_secret(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    me = service.get("/admin/me", headers={"X-Auth-Request-Email": "someone@bancoctt.pt"}).json()
    assert me["kind"] == "anonymous" and me["email"] is None
    me = service.get("/admin/me", headers={**PROXY, "X-Mcp-Proxy-Secret": "wrong"}).json()
    assert me["kind"] == "anonymous"
    assert service.put("/tools/echo", json=ECHO_TOOL, headers={"X-Auth-Request-Email": "someone@bancoctt.pt"}).status_code == 401


def test_signed_in_owner_is_admin_and_recorded_by_address(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    me = service.get("/admin/me", headers=PROXY).json()
    assert {k: me[k] for k in ("email", "kind", "label", "via", "admin")} == {
        "email": "antonio.s.cruz@bancoctt.pt", "kind": "admin", "label": "antonio.s.cruz@bancoctt.pt",
        "via": "proxy", "admin": True}
    assert me["name"] == "antonio.s.cruz" and me["picture"] is None      # no access token: the address's start
    assert me["sign_out"].startswith("/oauth2-entra/sign_out?rd=") and "logout_hint" not in me["sign_out"]
    r = service.put("/tools/echo", json=ECHO_TOOL, headers=PROXY)
    assert r.status_code == 200
    assert service.get("/tools/echo/history").json()["history"][-1]["actor"] == "antonio.s.cruz@bancoctt.pt"
    service.put("/tools/wecho", json=WRITE_TOOL, headers=PROXY)
    # a write-tier Try it by the signed-in administrator: allowed, recorded as the person, for the person
    r = service.post("/tools/wecho/invoke", json={"args": {"text": "x"}}, headers=PROXY)
    assert r.status_code == 200
    rec = service.get("/activity?tool=wecho&window=1h").json()["calls"][0]
    assert rec["caller"] == "antonio.s.cruz@bancoctt.pt" and rec["on_behalf_of"] == "antonio.s.cruz@bancoctt.pt"
    r = service.post("/apps/testapp/keys", json={"name": "from the console"}, headers=PROXY)
    assert r.status_code == 201


def test_admin_emails_restrict_who_may_write(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    monkeypatch.setenv("MCP_ADMIN_EMAILS", "logus2k@gmail.com, antonio.s.cruz@bancoctt.pt")
    other = {**PROXY, "X-Auth-Request-Email": "someone.else@bancoctt.pt"}
    me = service.get("/admin/me", headers=other).json()
    assert me["kind"] == "person" and me["admin"] is False
    assert service.put("/tools/echo", json=ECHO_TOOL, headers=other).status_code == 401
    assert service.put("/tools/echo", json=ECHO_TOOL, headers=PROXY).status_code == 200
    service.put("/tools/wecho", json=WRITE_TOOL, headers=PROXY)
    # a non-admin person may use read-tier tools, not write-tier ones
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers=other).status_code == 200
    assert service.post("/tools/wecho/invoke", json={"args": {"text": "x"}}, headers=other).status_code == 401
    monkeypatch.setenv("MCP_REQUIRE_KEYS", "1")
    # a signed-in person is not anonymous: still allowed read-tier tools when keys are required
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers=other).status_code == 200
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}).status_code == 401


def test_mcp_face_accepts_the_signed_in_admin(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    monkeypatch.setenv("MCP_REQUIRE_KEYS", "1")
    service.put("/tools/wecho", json=WRITE_TOOL, headers=PROXY)
    assert mcp_call(service, "testapp", "tools/list").status_code == 401
    r = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}}, headers=PROXY)
    assert r.status_code == 200 and r.json()["result"]["isError"] is False
    rec = service.get("/activity?tool=wecho&window=1h").json()["calls"][0]
    assert rec["caller"] == "antonio.s.cruz@bancoctt.pt" and rec["transport"] == "mcp"


def test_sign_out_hint_and_profile_switch(service, monkeypatch):
    import base64, json
    from app import identity
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    monkeypatch.setenv("MCP_IDENTITY_PROFILE", "0")             # no network in the test image
    claims = base64.urlsafe_b64encode(json.dumps({"login_hint": "O.abc=="}).encode()).decode().rstrip("=")
    id_token = f"eyJhbGciOiJSUzI1NiJ9.{claims}.sig"
    url = identity.sign_out_url("Bearer " + id_token)
    assert url.endswith("%26logout_hint%3DO.abc%253D%253D")        # the claim, encoded twice
    assert identity.sign_out_url("not a token") == identity.sign_out_url(None)
    me = service.get("/admin/me", headers={**PROXY, "X-Access-Token": "tok", "X-Id-Token": id_token}).json()
    assert me["name"] == "antonio.s.cruz" and me["picture"] is None and "logout_hint" in me["sign_out"]
