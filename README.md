# mcp-service

The domain's shared **tool and skill host**, with two faces and a console:

1. **Standard MCP** at `/mcp/{app}/` (Streamable HTTP, official `mcp` SDK). Any MCP
   client connects and gets `tools/list` · `tools/call` · `prompts/list` · `prompts/get` ·
   `resources/list` · `resources/read`. Tools carry annotations (read-only, destructive,
   idempotent) and optional output schemas; skills are served as prompts (with arguments)
   and as `skill://{name}` resources.
2. **Management REST**: CRUD for tools and skills, `POST /tools/{name}/invoke`,
   `GET /tools/manifest`, app keys, the invocation record, and record history.
3. **The Console** at `/admin` (on the domain: `/mcp-console/admin`, owner only): one page
   over both catalogs, the apps and their keys, the activity record and the settings.

Design and rules: [documents/console_specification.md](documents/console_specification.md).
Architecture: [documents/technical_architecture.md](documents/technical_architecture.md).
Identity and access (people, applications, agents): [documents/identity_and_access.md](documents/identity_and_access.md).

## Model
- **Tools** are declarative catalog entries (name, JSON Schema, which built-in `impl`,
  config, tier, the `apps` they are offered to, enabled). Implementations ship with the
  service (`app/toolimpl*.py`); the UI never authors executable code.
- **Skills** are reusable instructions several consumers must apply the same way
  (content, arguments, the apps they are offered to, the tools they expect, tags).
  App-tuned system prompts stay in their apps.
- A record is defined **once** and offered to several apps. Every write is versioned in
  `data/history.json`; any version can be diffed and restored.
- **App keys** (`mcpk_…`, one app each, fingerprints in `data/keys.json`) identify the
  caller on invoke and on MCP. Write-tier tools always need one; read-tier tools need one
  when `MCP_REQUIRE_KEYS=1`. `X-On-Behalf-Of` names the person the app acts for.
- **Every call is recorded** in `data/activity.db` (app, tool, caller, person, transport,
  outcome, duration, argument digest), kept `MCP_RETENTION_DAYS` (90).
- Arguments are **validated** against the tool's `input_schema` on both faces.

## Networks
- `cortex-kb` — Cortex reaches mcp-service (`web_search` for the Learning Assistant).
- `mcp_internal` — mcp-service reaches the isolated `websearch_server`.
- `ci-network` — the SDLC sensors reach Jenkins.
- `logus2k_network` — the SDLC wall reaches this service.
- `noted-network` — this machine only (`docker-compose.local.yml`): job2cool and the
  other apps here.

## REST quick-ref
```
GET    /health                         GET /backends/health
GET    /tools[?app=]                   GET /tools/manifest?app=        GET /tools/{name}
PUT    /tools/{name}[?app=]  (admin)   PATCH /tools/{name}/enabled     DELETE /tools/{name}[?app=]
POST   /tools/{name}/invoke?app=       {"args": {...}}   Authorization: Bearer mcpk_…   X-On-Behalf-Of: person
GET    /tools/{name}/history           POST /tools/{name}/restore {"version": n}  (admin)
GET    /skills[?app=]   PUT/PATCH/DELETE as for tools   POST /skills/{name}/render {"arguments": {...}}
GET    /apps                           GET /apps/{app}/keys
POST   /apps/{app}/keys  (admin)       DELETE /apps/{app}/keys/{id}  (admin)
GET    /activity?window=24h&app=&tool=&caller=&ok=&q=&cursor=     GET /activity/summary?window=   GET /activity.csv
GET    /admin  /admin/registry  /admin/health  /admin/attention  /admin/export[?app=]
```
Writes need `Authorization: Bearer <MCP_ADMIN_TOKEN>` (from `./.env`), or the domain
proxy's signed-in administrator (Microsoft Entra ID; see Sign-in). Reads are open on the
internal network.

## The Console's shell and Help
The console wears Cortex's and Slides' shell (Banco CTT tokens, the self-hosted Inter, the wordmark with
"MCP SERVER" under it, the collapsible side menu with Settings at the bottom, the top menu bar, the profile
with photo and name at the right, the status bar). **Help** holds the **User Manual** (`app/help/manual/`, one
page per task), the **Integration Guide** (`app/help/guide/`: how an app or an agent connects) and the
**Technical Architecture** (`documents/`), rendered in the console by the same Markdown viewer Cortex uses. The interface and the User Manual exist in
English and in European Portuguese (the profile's menu switches; `app/static/pt.js` is the dictionary).

## OAuth 2.1 for MCP clients
MCP clients in a person's hands (Claude Code, claude.ai connectors, SDK clients) use the standard flow: the
public MCP endpoint `https://logus2k.com/mcp-console/mcp/{app}/` answers 401 with the resource metadata, the client
registers itself (RFC 7591), the person signs in through the domain's Entra proxy and allows the client on a consent
page, and the client gets a token for that person (scopes `tools:read`, `tools:write`, `admin`). Registered clients
are managed in Settings › OAuth clients. A program gets a **machine client** bound to its app (Apps › New machine
client) and the client credentials grant: an expiring token that acts as the app, no person behind it. Keys remain
for programs that cannot run the exchange. See `app/oauth.py` and the
Integration Guide, "Sign in with OAuth 2.1".

## The application catalog
An app is a record (owner, contact, status, tags, versioned). Tools and skills are offered to registered apps only,
keys are issued to them only, and a retired app answers nobody. Apps › New app registers one; the apps that existed
before the catalog were registered automatically.

## Sign-in (Microsoft Entra ID)
On the domain the console is at `https://logus2k.com/mcp-console/admin`, behind
oauth2-proxy-entra (`proxy_server/conf/route-mcp-console.conf`, allow-list
`/oauth2-entra/auth-admin`). The proxy forwards `X-Auth-Request-Email` with
`X-Mcp-Proxy-Secret`; the service trusts the address only with that secret
(`MCP_PROXY_SECRET` in `./.env`, the same value in `proxy_server/conf/secrets/mcp-console.conf`).
`MCP_ADMIN_EMAILS` names who may write; a signed-in administrator needs no token, and
every write and Try it is recorded by their address. `GET /admin/me` says who you are.

## Run
```sh
docker network create mcp_internal   # shared with websearch_server (once)
docker compose up -d --build
curl -s localhost:4950/health
open http://localhost:4950/admin     # the Console; paste the admin token for writes
```
Tests run inside the image: `docker build --target test .`

## Connect an app or an MCP client
In the Console, **Apps › New key** issues the app's key (shown once). Then:
```sh
claude mcp add --transport http tutor https://logus2k.com/mcp-service/mcp/tutor/ --header "Authorization: Bearer mcpk_…"
curl -s -X POST localhost:4950/tools/web_search/invoke?app=tutor -H 'Authorization: Bearer mcpk_…' \
     -H 'X-On-Behalf-Of: person@example.com' -H 'content-type: application/json' \
     -d '{"args":{"query":"kubernetes operator pattern","max_results":3}}'
```
The Connect tab of any tool shows the same snippets for curl, Python, Claude Code and
Claude Desktop.

## Environment
| Variable | Default | Meaning |
|---|---|---|
| `MCP_ADMIN_TOKEN` | empty (open, dev) | bearer for writes and the console's Try it |
| `MCP_REQUIRE_KEYS` | `0` | `1`: every invoke and MCP call needs an app key |
| `MCP_PROXY_SECRET` | empty (identity off) | trust `X-Auth-Request-Email` only with this secret from the proxy |
| `MCP_ADMIN_EMAILS` | empty (anyone admitted) | who may write when signed in through the proxy, and who may use `tools:write` / `admin` over OAuth |
| `MCP_PUBLIC_URL` | `https://logus2k.com/mcp-console` | the OAuth issuer and the resource's public address |
| `MCP_OAUTH_SIGNING_KEY` | generated into `data/oauth_signing.key` | signs the access tokens |
| `MCP_RECORD_ARGS` | `0` | `1`: keep read-tier arguments in the record (digests otherwise) |
| `MCP_RETENTION_DAYS` | `90` | activity rows kept |
| `WEBSEARCH_URL`, `NEWSAPI_KEY`, `JENKINS_URL`, `PROXY_CONF_DIR`, `PROXY_CONTAINER`, `SDLC_*` | see compose | backends of the shipped implementations |
