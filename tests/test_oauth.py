"""OAuth 2.1 end to end: metadata, dynamic registration, the code flow with PKCE behind the
proxy's sign-in, tokens on both faces, scopes, refresh rotation, revocation, the public path."""
from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

from conftest import ECHO_TOOL, WRITE_TOOL, mcp_call

PROXY = {"X-Mcp-Proxy-Secret": "proxy-secret", "X-Auth-Request-Email": "antonio.s.cruz@bancoctt.pt"}
REDIRECT = "http://localhost:51234/callback"


def _pkce():
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def _register(service, method="none"):
    r = service.post("/oauth/register", json={"client_name": "Test client", "redirect_uris": [REDIRECT],
                                               "token_endpoint_auth_method": method})
    assert r.status_code == 201, r.text
    return r.json()


def _authorize(service, client, scope="tools:read", user=PROXY, resource=None):
    verifier, challenge = _pkce()
    params = {"response_type": "code", "client_id": client["client_id"], "redirect_uri": REDIRECT, "scope": scope,
              "state": "xyz", "code_challenge": challenge, "code_challenge_method": "S256"}
    if resource:
        params["resource"] = resource
    r = service.get("/oauth/authorize", params=params, headers=user)
    assert r.status_code == 200 and 'name="rid"' in r.text and "Allow" in r.text, r.text[:300]
    rid = r.text.split('name="rid" value="')[1].split('"')[0]
    r = service.post("/oauth/decision", data={"rid": rid, "decision": "allow"}, headers=user, follow_redirects=False)
    assert r.status_code == 302
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["state"] == ["xyz"] and "code" in q
    return q["code"][0], verifier


def _tokens(service, client, code, verifier, secret=None):
    form = {"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
            "client_id": client["client_id"], "code_verifier": verifier}
    if secret:
        form["client_secret"] = secret
    r = service.post("/oauth/token", data=form)
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["token_type"] == "Bearer" and t["access_token"].startswith("eyJ") and t["refresh_token"].startswith("mcpr_")
    return t


def test_metadata(service, monkeypatch):
    monkeypatch.setenv("MCP_PUBLIC_URL", "http://testserver")
    m = service.get("/.well-known/oauth-authorization-server").json()
    assert m["issuer"] == "http://testserver" and m["token_endpoint"] == "http://testserver/oauth/token"
    assert m["code_challenge_methods_supported"] == ["S256"] and "registration_endpoint" in m
    r = service.get("/.well-known/oauth-protected-resource").json()
    assert r["resource"] == "http://testserver/mcp/" and r["authorization_servers"] == ["http://testserver"]
    r = service.get("/.well-known/oauth-protected-resource/mcp/tutor/").json()
    assert r["resource"] == "http://testserver/mcp/tutor/"


def test_registration_rules(service):
    r = service.post("/oauth/register", json={"redirect_uris": ["http://evil.example/cb"]})
    assert r.status_code == 400 and r.json()["error"] == "invalid_redirect_uri"
    r = service.post("/oauth/register", json={"redirect_uris": ["https://claude.ai/api/mcp/auth_callback"]})
    assert r.status_code == 201 and r.json()["client_id"].startswith("mcpc_") and "client_secret" not in r.json()
    c = _register(service, "client_secret_post")
    assert c["client_secret"] and c["token_endpoint_auth_method"] == "client_secret_post"
    listed = service.get("/oauth/clients").json()["clients"]
    assert all("secret_hash" not in x for x in listed) and len(listed) == 2


def test_code_flow_and_tokens_on_both_faces(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    monkeypatch.setenv("MCP_PUBLIC_URL", "http://testserver")
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    client = _register(service)
    # the consent page needs the signed-in person
    assert service.get("/oauth/authorize", params={"client_id": client["client_id"]}).status_code == 401
    code, verifier = _authorize(service, client)
    # a wrong verifier, then the real one; the code is single-use
    r = service.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
                                           "client_id": client["client_id"], "code_verifier": "x" * 50})
    assert r.status_code == 400 and r.json()["error"] == "invalid_grant"
    code, verifier = _authorize(service, client)
    t = _tokens(service, client, code, verifier)
    r = service.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
                                           "client_id": client["client_id"], "code_verifier": verifier})
    assert r.status_code == 400
    bearer = {"Authorization": f"Bearer {t['access_token']}"}
    # MCP face
    tools = mcp_call(service, "testapp", "tools/list", headers=bearer).json()["result"]["tools"]
    assert [x["name"] for x in tools] == ["echo"]
    res = mcp_call(service, "testapp", "tools/call", {"name": "echo", "arguments": {"text": "hi"}}, headers=bearer).json()["result"]
    assert res["isError"] is False
    rec = service.get("/activity?tool=echo&window=1h").json()["calls"][0]
    assert rec["caller"] == "oauth:antonio.s.cruz@bancoctt.pt" and rec["on_behalf_of"] == "antonio.s.cruz@bancoctt.pt" and rec["transport"] == "mcp"
    # REST face
    r = service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers=bearer)
    assert r.status_code == 200
    # a tampered token
    bad = {"Authorization": "Bearer " + t["access_token"][:-3] + "abc"}
    r = mcp_call(service, "testapp", "tools/list", headers=bad)
    assert r.status_code == 401 and "resource_metadata=" in r.headers["www-authenticate"]


def test_scopes_and_administrators(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    monkeypatch.setenv("MCP_ADMIN_EMAILS", "antonio.s.cruz@bancoctt.pt")
    service.put("/tools/wecho", json=WRITE_TOOL, headers=service.admin)
    client = _register(service)
    # read scope only: a write tool is refused with 403
    code, verifier = _authorize(service, client, "tools:read")
    t = _tokens(service, client, code, verifier)
    res = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}},
                   headers={"Authorization": f"Bearer {t['access_token']}"}).json()["result"]
    assert res["isError"] is True and "tools:write" in res["content"][0]["text"]
    assert service.put("/tools/wecho", json={"description": "no"}, headers={"Authorization": f"Bearer {t['access_token']}"}).status_code == 401
    # write + admin scopes for an administrator
    code, verifier = _authorize(service, client, "tools:read tools:write admin")
    t = _tokens(service, client, code, verifier)
    b = {"Authorization": f"Bearer {t['access_token']}"}
    assert mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}}, headers=b).json()["result"]["isError"] is False
    assert service.put("/tools/wecho", json={"description": "changed over OAuth"}, headers=b).status_code == 200
    assert service.get("/tools/wecho/history").json()["history"][-1]["actor"] == "oauth:antonio.s.cruz@bancoctt.pt"
    # the same scopes for someone not on the administrator list: write refused
    other = {**PROXY, "X-Auth-Request-Email": "someone@bancoctt.pt"}
    code, verifier = _authorize(service, client, "tools:read tools:write admin", user=other)
    t = _tokens(service, client, code, verifier)
    b = {"Authorization": f"Bearer {t['access_token']}"}
    res = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}}, headers=b).json()["result"]
    assert res["isError"] is True and "administrators" in res["content"][0]["text"]
    assert service.put("/tools/wecho", json={"description": "no"}, headers=b).status_code == 401
    # an unknown scope is refused at authorization
    r = service.get("/oauth/authorize", params={"response_type": "code", "client_id": client["client_id"], "redirect_uri": REDIRECT,
                                                 "scope": "everything", "code_challenge": "c" * 43, "code_challenge_method": "S256"}, headers=PROXY)
    assert r.status_code == 400 and r.json()["error"] == "invalid_scope"


def test_refresh_rotation_and_revocation(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    client = _register(service, "client_secret_post")
    code, verifier = _authorize(service, client)
    t = _tokens(service, client, code, verifier, client["client_secret"])
    # without the secret the confidential client is refused
    r = service.post("/oauth/token", data={"grant_type": "refresh_token", "refresh_token": t["refresh_token"], "client_id": client["client_id"]})
    assert r.status_code == 401 and r.json()["error"] == "invalid_client"
    r = service.post("/oauth/token", data={"grant_type": "refresh_token", "refresh_token": t["refresh_token"],
                                           "client_id": client["client_id"], "client_secret": client["client_secret"]})
    assert r.status_code == 200
    t2 = r.json()
    assert t2["refresh_token"] != t["refresh_token"]
    # the old refresh token is gone (rotation); the new one can be revoked
    r = service.post("/oauth/token", data={"grant_type": "refresh_token", "refresh_token": t["refresh_token"],
                                           "client_id": client["client_id"], "client_secret": client["client_secret"]})
    assert r.status_code == 400 and r.json()["error"] == "invalid_grant"
    assert service.post("/oauth/revoke", data={"token": t2["refresh_token"], "client_id": client["client_id"],
                                               "client_secret": client["client_secret"]}).status_code == 200
    r = service.post("/oauth/token", data={"grant_type": "refresh_token", "refresh_token": t2["refresh_token"],
                                           "client_id": client["client_id"], "client_secret": client["client_secret"]})
    assert r.status_code == 400
    # deleting the client (console) ends everything of its
    assert service.delete(f"/oauth/clients/{client['client_id']}", headers=service.admin).json()["deleted"] is True
    assert service.get("/oauth/clients").json()["clients"] == []


def test_public_path_is_never_anonymous(service):
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    r = mcp_call(service, "testapp", "tools/list", headers={"X-Mcp-Public": "1"})
    assert r.status_code == 401 and r.headers["www-authenticate"].startswith("Bearer ") and "resource_metadata=" in r.headers["www-authenticate"]
    r = service.post("/tools/echo/invoke", json={"args": {"text": "x"}}, headers={"X-Mcp-Public": "1"})
    assert r.status_code == 401 and "resource_metadata=" in r.headers["www-authenticate"]
    # inside the network, keys optional: still answered
    assert service.post("/tools/echo/invoke", json={"args": {"text": "x"}}).status_code == 200


def test_consent_denied(service, monkeypatch):
    monkeypatch.setenv("MCP_PROXY_SECRET", "proxy-secret")
    client = _register(service)
    verifier, challenge = _pkce()
    r = service.get("/oauth/authorize", params={"response_type": "code", "client_id": client["client_id"], "redirect_uri": REDIRECT,
                                                 "state": "s1", "code_challenge": challenge, "code_challenge_method": "S256"}, headers=PROXY)
    rid = r.text.split('name="rid" value="')[1].split('"')[0]
    r = service.post("/oauth/decision", data={"rid": rid, "decision": "deny"}, headers=PROXY, follow_redirects=False)
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["error"] == ["access_denied"] and q["state"] == ["s1"]
    # another person cannot answer someone else's pending request
    r = service.get("/oauth/authorize", params={"response_type": "code", "client_id": client["client_id"], "redirect_uri": REDIRECT,
                                                 "code_challenge": challenge, "code_challenge_method": "S256"}, headers=PROXY)
    rid = r.text.split('name="rid" value="')[1].split('"')[0]
    r = service.post("/oauth/decision", data={"rid": rid, "decision": "allow"}, headers={**PROXY, "X-Auth-Request-Email": "x@bancoctt.pt"}, follow_redirects=False)
    assert r.status_code == 400


def test_client_credentials_for_machine_clients(service, monkeypatch):
    monkeypatch.setenv("MCP_PUBLIC_URL", "http://testserver")
    service.put("/tools/echo", json=ECHO_TOOL, headers=service.admin)
    service.put("/tools/wecho", json=WRITE_TOOL, headers=service.admin)
    # dynamic registration cannot ask for the grant; an administrator registers a machine client for an app
    r = service.post("/oauth/register", json={"redirect_uris": [REDIRECT], "grant_types": ["client_credentials"]})
    assert r.status_code == 400 and r.json()["error"] == "invalid_client_metadata"
    assert service.post("/apps/testapp/clients", json={"name": "nightly job"}).status_code == 401
    assert service.post("/apps/nope/clients", json={"name": "x"}, headers=service.admin).status_code == 400
    r = service.post("/apps/testapp/clients", json={"name": "nightly job", "scopes": ["tools:read"]}, headers=service.admin)
    assert r.status_code == 201, r.text
    mc = r.json()
    assert mc["client_id"].startswith("mcpm_") and mc["client_secret"] and mc["kind"] == "machine" and mc["app"] == "testapp"
    assert "client_credentials" in service.get("/.well-known/oauth-authorization-server").json()["grant_types_supported"]
    # the grant: secret required, scopes limited, no refresh token
    r = service.post("/oauth/token", data={"grant_type": "client_credentials", "client_id": mc["client_id"]})
    assert r.status_code == 401
    r = service.post("/oauth/token", data={"grant_type": "client_credentials", "client_id": mc["client_id"],
                                           "client_secret": mc["client_secret"], "scope": "tools:write"})
    assert r.status_code == 400 and r.json()["error"] == "invalid_scope"
    r = service.post("/oauth/token", data={"grant_type": "client_credentials", "client_id": mc["client_id"], "client_secret": mc["client_secret"]})
    assert r.status_code == 200
    t = r.json()
    assert t["scope"] == "tools:read" and "refresh_token" not in t
    b = {"Authorization": f"Bearer {t['access_token']}"}
    # acts as the app: its endpoint yes, another app's no; read yes, write no (scope)
    assert mcp_call(service, "testapp", "tools/list", headers=b).status_code == 200
    assert mcp_call(service, "other", "tools/list", headers=b).status_code == 403
    res = mcp_call(service, "testapp", "tools/call", {"name": "echo", "arguments": {"text": "hi"}}, headers=b).json()["result"]
    assert res["isError"] is False
    rec = service.get("/activity?tool=echo&window=1h").json()["calls"][0]
    assert rec["caller"] == f"client:{mc['client_id']}" and rec["app"] == "testapp" and rec["on_behalf_of"] == ""
    res = mcp_call(service, "testapp", "tools/call", {"name": "wecho", "arguments": {"text": "x"}}, headers=b).json()["result"]
    assert res["isError"] is True and "tools:write" in res["content"][0]["text"]
    # a client registered with tools:write may write; REST too
    mc2 = service.post("/apps/testapp/clients", json={"name": "deployer", "scopes": ["tools:read", "tools:write"]}, headers=service.admin).json()
    t2 = service.post("/oauth/token", data={"grant_type": "client_credentials", "client_id": mc2["client_id"], "client_secret": mc2["client_secret"]}).json()
    b2 = {"Authorization": f"Bearer {t2['access_token']}"}
    assert service.post("/tools/wecho/invoke", json={"args": {"text": "x"}}, headers=b2).status_code == 200
    # never an administrator
    assert service.put("/tools/wecho", json={"description": "no"}, headers=b2).status_code == 401
    # the app's view lists its machine clients; a retired app refuses the grant; removal kills the token
    view = service.get("/apps/testapp").json()
    assert [c["client_name"] for c in view["clients"]] == ["nightly job", "deployer"] and all("secret_hash" not in c for c in view["clients"])
    service.put("/apps/testapp", json={"status": "retired"}, headers=service.admin)
    r = service.post("/oauth/token", data={"grant_type": "client_credentials", "client_id": mc["client_id"], "client_secret": mc["client_secret"]})
    assert r.status_code == 400 and r.json()["error"] == "unauthorized_client"
    service.put("/apps/testapp", json={"status": "active"}, headers=service.admin)
    assert service.delete(f"/apps/testapp/clients/{mc2['client_id']}", headers=service.admin).json()["deleted"] is True
    assert mcp_call(service, "testapp", "tools/list", headers=b2).status_code == 401
    assert mcp_call(service, "testapp", "tools/list", headers=b).status_code == 200
