# Identity and access: people, applications and agents

How the MCP server knows **who is calling** and decides **what they may do**, for the
three kinds of caller it serves, and how the planned domain sign-in service (Dex) fits in.

Status: the MCP side (OAuth 2.1 server, app keys, machine clients, the catalog) is
implemented in `app/auth.py`, `app/oauth.py`, `app/keys.py` and `app/registry.py`. The
domain sign-in service (Dex, its proxy and the per-application sign-in page) is the agreed
design, not yet built; today the console is gated by the Entra-only proxy.

## 1. The parts

| Part | Where | Job |
|---|---|---|
| **Dex** | `assets/dex`, its own container | The domain's single identity provider. Authenticates a person against Microsoft Entra ID, Google or a local email-and-password account and issues an OpenID Connect identity to the proxy. |
| **oauth2-proxy-dex** | `assets/proxy_server` | Holds the person's session for the domain and answers nginx's "who is this?" sub-request with the person's address and name. |
| **Sign-in page** | `assets/proxy_server` | Shown only when an application offers several providers. Reads one configuration file that says which providers each application offers and sends the person to Dex with the chosen one. One provider: no page, straight through. |
| **nginx** | `assets/proxy_server` | Gates each application's routes with an allow-list, forwards the identity headers, and marks the MCP server's public locations. |
| **mcp-service** | this project | Both an **OAuth 2.1 authorization server** (issues tokens to MCP clients and to machine clients) and a **protected resource** (the tool and skill endpoints that check those tokens, keys or the proxy's identity). |
| **Application catalog** | `data/registry.json` | Every application is a record. Keys and machine clients are issued to registered, active applications only. |

Dex is the only place a password or a provider login is ever handled. mcp-service never
sees a person's credentials; it only receives, from the proxy, an address it can trust
because the request also carries the proxy secret.

## 2. Three kinds of caller

| Caller | Example | Authenticates with | mcp-service sees | May do |
|---|---|---|---|---|
| **Person** at the console | an administrator in the browser | Dex sign-in, session held by the proxy | `X-Auth-Request-Email` with the proxy secret | Reads for anyone admitted; writes and Try it only for addresses on `MCP_ADMIN_EMAILS`. Recorded by address. |
| **Agent acting for a person** | Claude Code, claude.ai connector, an SDK client on someone's laptop | OAuth 2.1 authorization code with PKCE, after the person signs in through Dex and allows the client | Access token signed by mcp-service, scopes `tools:read`, `tools:write`, `admin` | What the scopes allow, never more than the person could do. Recorded as `oauth:<address>`. |
| **Application or autonomous agent** | Cortex's learning API, the SDLC wall, a scheduled agent | A **machine client** and the client credentials grant, or an **app key** for programs that cannot run the exchange | Token with subject `app:<name>`, or `mcpk_…` key bound to one app | Only the tools offered to its application; writes need `tools:write` on the client. Recorded as `client:<id>` or by key id, plus `X-On-Behalf-Of` naming the person it acts for. |

Anonymous calls are accepted for read-tier tools only on the internal network and only
while `MCP_REQUIRE_KEYS` is not `1`. Nothing anonymous ever reaches a write-tier tool or
the public path.

## 3. How the parts connect

```mermaid
flowchart LR
    subgraph Callers
        P["Person<br/>browser"]
        A["Agent for a person<br/>Claude Code, SDK client"]
        M["Application or<br/>autonomous agent"]
    end

    subgraph Proxy["Domain proxy, assets/proxy_server"]
        N["nginx<br/>routes and allow-lists"]
        S["Sign-in page<br/>providers per application"]
        O["oauth2-proxy-dex<br/>session"]
    end

    subgraph Identity["assets/dex"]
        D["Dex<br/>OpenID Connect provider"]
    end

    subgraph Providers
        E["Microsoft Entra ID"]
        G["Google"]
        L["Local accounts"]
    end

    subgraph MCP["mcp-service"]
        AS["OAuth 2.1 server<br/>/oauth/*, /.well-known/*"]
        RS["Protected resource<br/>/mcp/{app}/, /tools/*/invoke"]
        C["Console<br/>/admin"]
        R["Catalog, keys,<br/>machine clients"]
    end

    P --> N
    N -- "no session" --> O
    O --> S
    S -- "connector_id" --> D
    D --> E
    D --> G
    D --> L
    O -- "X-Auth-Request-Email<br/>+ proxy secret" --> C
    A -- "401 + resource metadata" --> RS
    A -- "authorize (gated like the console)" --> N
    A -- "token" --> AS
    A -- "Bearer access token" --> RS
    M -- "client credentials" --> AS
    M -- "Bearer token or mcpk_ key" --> RS
    AS --- R
    RS --- R
```

## 4. A person signs in to the console

The person sees, at most, two screens: the sign-in page with the application's providers
and the chosen provider's own login. If the application offers one provider, only the
provider's login appears.

```mermaid
sequenceDiagram
    autonumber
    actor U as Person
    participant N as nginx
    participant O as oauth2-proxy-dex
    participant S as Sign-in page
    participant D as Dex
    participant I as Provider (Entra, Google or local)
    participant C as Console

    U->>N: GET /mcp-console/admin
    N->>O: auth sub-request
    O-->>N: no session
    N-->>U: redirect to sign-in
    U->>S: GET /signin?app=mcp-console
    alt application offers several providers
        S-->>U: chooser with that application's providers
        U->>S: picks one
    else one provider
        Note over S: no page, immediate redirect
    end
    S->>D: /dex/auth with connector_id
    D->>I: provider login
    I-->>D: identity (address, name, picture)
    D-->>O: OpenID Connect code, then id token
    O->>O: allow-list for /mcp-console
    O-->>U: session cookie, redirect to /mcp-console/admin
    U->>N: GET /mcp-console/admin
    N->>O: auth sub-request
    O-->>N: X-Auth-Request-Email, name
    N->>C: request + X-Mcp-Proxy-Secret
    C->>C: caller = person, admin if on MCP_ADMIN_EMAILS
    C-->>U: the console, profile with name and photo
```

What each step decides:

- **The proxy's allow-list** (step 12) decides whether this identity may enter the
  application at all, whichever provider it came from.
- **The proxy secret** (step 17) is why mcp-service trusts the address header: it is set
  in the route and nowhere else, so nothing on the internal network can name a person.
- **`MCP_ADMIN_EMAILS`** (step 18) decides whether the person may write.

## 5. An agent acting for a person connects over MCP

This is the standard MCP authorization flow (OAuth 2.1 with PKCE, RFC 8414 and RFC 9728
metadata, RFC 7591 dynamic registration). The person signs in through Dex exactly as for
the console, because the authorize endpoint sits behind the same gate, then allows the
client on mcp-service's consent page.

```mermaid
sequenceDiagram
    autonumber
    actor U as Person
    participant A as MCP client (Claude Code, SDK)
    participant RS as mcp-service resource /mcp/{app}/
    participant AS as mcp-service OAuth server
    participant G as Dex gate (proxy)

    A->>RS: POST initialize, no token
    RS-->>A: 401, WWW-Authenticate with resource_metadata
    A->>AS: GET /.well-known/oauth-protected-resource/mcp-console/
    AS-->>A: authorization server address, scopes
    A->>AS: GET /.well-known/oauth-authorization-server/mcp-console
    AS-->>A: endpoints, PKCE S256, grants
    A->>AS: POST /oauth/register (dynamic client registration)
    AS-->>A: client_id
    A->>U: open browser at /oauth/authorize with code_challenge
    U->>G: not signed in
    G-->>U: Dex sign-in (section 4)
    U->>AS: /oauth/authorize as a signed-in person
    AS-->>U: consent page: client, scopes
    U->>AS: allow
    AS-->>A: redirect with code
    A->>AS: POST /oauth/token, code + code_verifier
    AS-->>A: access token (scopes, aud = /mcp/{app}/), refresh token
    A->>RS: POST tools/call, Bearer access token
    RS->>RS: verify signature, issuer, audience, client still registered
    RS->>RS: enforce: tool offered to app, tier vs scopes, admin list for write
    RS-->>A: result, recorded as oauth:<address>
```

The token acts **for the person**: `tools:write` and `admin` are granted only to people on
`MCP_ADMIN_EMAILS`, so an agent can never do more than the person who allowed it. Refresh
tokens rotate; a revoked or deleted client makes all its tokens useless at once.

## 6. An application or an autonomous agent calls a tool

No person is in the loop. The application is registered in the catalog, and an
administrator issues it either a machine client (preferred, expiring tokens) or an app key
(for programs that cannot run the token exchange). Both are bound to **one** application.

```mermaid
sequenceDiagram
    autonumber
    participant Adm as Administrator (console)
    participant AS as mcp-service OAuth server
    participant App as Application or agent
    participant RS as mcp-service resource

    Adm->>AS: Apps › New machine client (app, scopes)
    AS-->>Adm: client_id mcpm_…, secret shown once
    Note over App: secret kept in the application's own .env
    App->>AS: POST /oauth/token, grant_type=client_credentials
    AS->>AS: client exists, app active in the catalog
    AS-->>App: access token, sub = app:<name>, aud = /mcp/<app>/
    App->>RS: tools/call with Bearer token, X-On-Behalf-Of: person
    RS->>RS: token's app = path's app, tool offered to app, write needs tools:write
    RS-->>App: result, recorded as client:<id> for <person>
```

With an app key the exchange is skipped: the key itself is the bearer, and the same checks
apply (key's app equals the path's app, tool offered to that app). Retiring an application
in the catalog refuses its keys and clients immediately.

## 7. The authorization decision

Every call, on both faces (MCP and REST invoke), goes through the same decision after the
caller is resolved. Simplified from `enforce` in `app/auth.py`:

```mermaid
flowchart TD
    start([call for tool T under app X]) --> who{who is calling}
    who -- "key or machine client" --> bound{bound to app X?}
    bound -- no --> f403a[403 belongs to another app]
    bound -- yes --> offered
    who -- "admin, person,<br/>oauth, anonymous" --> offered{T offered to X<br/>and enabled?}
    offered -- no --> f404[404 not offered]
    offered -- yes --> kind{caller kind}
    kind -- admin --> ok
    kind -- key --> ok
    kind -- machine --> mw{write tier?}
    mw -- "no" --> ok
    mw -- "yes" --> ms{tools:write<br/>on the client?}
    ms -- yes --> ok
    ms -- no --> f403b[403 scope]
    kind -- oauth --> ow{write tier?}
    ow -- "yes" --> os{tools:write and<br/>person on admin list?}
    os -- yes --> ok
    os -- no --> f403c[403 scope]
    ow -- "no" --> or{any tools scope?}
    or -- yes --> ok
    or -- no --> f403d[403 scope]
    kind -- "person or anonymous" --> pw{write tier?}
    pw -- yes --> f401a[401 needs a key or admin]
    pw -- no --> pk{keys required<br/>or public path,<br/>and anonymous?}
    pk -- yes --> f401b[401 with WWW-Authenticate]
    pk -- no --> ok([run, validate args, record])
```

## 8. Which providers an application offers

One file beside the proxy routes, one entry per application:

```yaml
default: { providers: [microsoft, google, local] }
apps:
  mcp-console: { name: "MCP Server", providers: [microsoft, google, local] }
  cortex:      { name: "Cortex",     providers: [microsoft] }
  job2cool:    { name: "job2cool",   providers: [google, local] }
providers:
  microsoft: { label: "Microsoft",          connector: microsoft }
  google:    { label: "Google",             connector: google }
  local:     { label: "Email and password", connector: local }
```

```mermaid
flowchart LR
    req([sign-in for application X]) --> n{providers<br/>configured for X}
    n -- "none listed" --> d[use default set]
    d --> count
    n -- listed --> count{how many?}
    count -- one --> direct[redirect to Dex with that connector_id]
    count -- "two or more" --> page[chooser page with those providers only]
    page --> pick[person picks one]
    pick --> direct
    direct --> dex[Dex sends the person to the provider]
```

The chooser limits what is offered; it does not enforce. Whoever reaches Dex by another
route still meets the application's allow-list, which is where an unwanted identity is
refused.

## 9. Where things are recorded and revoked

| Thing | Issued where | Revoked where | Effect |
|---|---|---|---|
| Person's session | oauth2-proxy-dex | sign out in the profile menu (proxy sign-out) | next request needs a sign-in |
| OAuth client (agent for a person) | `/oauth/register` by the client | Settings › OAuth clients | all its tokens refused |
| Access and refresh tokens | `/oauth/token` | `/oauth/revoke`, or client deletion | token refused on next call |
| Machine client | Apps › New machine client | Apps › client's Delete | client credentials refused |
| App key | Apps › New key | Apps › key's Revoke | key refused |
| Application | Apps › New app | Apps › Retire | keys, clients and offers refused |

Every call is written to the activity record with the caller as resolved above, so the
Activity view answers "which person, through which client or application, called what".
