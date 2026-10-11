# Sign in with OAuth 2.1

For an MCP client that acts for a **person** (Claude Code, claude.ai's custom connectors, an agent in someone's
hands), the service is an OAuth 2.1 **resource server** and hosts its own **authorization server**, the shape the MCP
specification prescribes. The person signs in with Microsoft Entra ID through the domain proxy; the client gets a
token for that person; every call is recorded under their address.

## What a client does

1. Calls the MCP endpoint, `https://logus2k.com/mcp-console/mcp/{app}/`, and gets `401` with
   `WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource"`.
2. Reads that metadata (RFC 9728), which names the authorization server, then the server's metadata (RFC 8414) at
   `https://logus2k.com/mcp-console/.well-known/oauth-authorization-server`.
3. Registers itself (RFC 7591) at `/oauth/register`: a name and its redirect URIs (`https://…`, or
   `http://localhost:<port>/…` for a native client). Public clients need no secret; PKCE protects the code.
4. Sends the person to `/oauth/authorize` with `code_challenge` (S256), the `scope` and the `resource` (the MCP
   endpoint). The proxy signs the person in; the consent page shows the client's name and what it asks; the person
   allows or denies.
5. Exchanges the code at `/oauth/token` with its `code_verifier`, and receives an access token (1 hour) and a refresh
   token (30 days, rotated on each use).
6. Sends `Authorization: Bearer <access token>` on every request; refreshes when it expires; revokes at
   `/oauth/revoke` when done.

Claude Code and claude.ai do all of this themselves: give them the endpoint's address and sign in when asked.

## Scopes

| Scope | Grants |
|---|---|
| `tools:read` (the default) | read-tier tools, as the person |
| `tools:write` | write-tier tools too, for people on the administrator list |
| `admin` | the console's writes over REST, for people on the administrator list |

A token for someone not on the administrator list may hold `tools:write` or `admin` and still be refused those
actions with `403`: the list decides, the scope only asks.

## The record

A call over OAuth is recorded with the caller `oauth:<address>` and the same address as the person acted for. The
console lists the registered clients in **Settings › OAuth clients**, where an administrator removes one; removal ends
its refresh tokens.

## Errors

| Status | Meaning |
|---|---|
| `401` + `WWW-Authenticate` | no token, or an invalid or expired one: start (or refresh) the flow |
| `403 a write-tier tool needs the tools:write scope` | ask for the scope at authorization |
| `403 … for administrators` | the person is not on the administrator list |
| `400 invalid_grant` | the code was used, expired, or the PKCE verifier did not match |
| `400 invalid_redirect_uri` | registration with a redirect that is neither https nor localhost |

## A program: the client credentials grant

A program that speaks for an **app** (a daemon, a backend, a scheduled job) does not sign a person in. An
administrator registers it as a **machine client** of the app in the console (**Apps › New machine client**), bound
to the scopes it may use; the id and secret are shown once. The program then asks for a token with its own
credentials, no browser involved:

```bash
curl -s -X POST https://logus2k.com/mcp-console/oauth/token \
  -d grant_type=client_credentials -d client_id=mcpm_… -d client_secret=… -d scope=tools:read
# {"access_token": "eyJ…", "token_type": "Bearer", "expires_in": 3600, "scope": "tools:read"}
```

The token acts as the app, for one hour, within the client's scopes; there is no refresh token, the program asks
again. It is accepted on the app's endpoint only and refused on any other app's; a retired app's clients get no
token; removing the client in the console ends its tokens at once. Calls are recorded as `client:<id>` for the app,
with no person.

Dynamic registration cannot create a machine client: a machine speaks for an app, and nobody consents on its behalf,
so an administrator binds it. Compared with a **key**, a machine client's token expires and its scopes are explicit;
compared with the interactive flow, nothing identifies a person.

## Keys or OAuth?

A **key** or a **machine client** identifies a program: a daemon, a backend, a scheduled job. The interactive flow
identifies a person through a program: an interactive agent, a hosted connector. All reach the same endpoint; the
record tells them apart (`<key id>`, `client:<id>`, `oauth:<address>`).

## See also
- [Connect over MCP](04-connect-over-mcp.md)
- [Keys and identity](02-keys-and-identity.md)
