# mcp-service — Technical Architecture

Updated 2026-10-10 to the state delivered by
[console_specification.md](console_specification.md). The earlier version of this
document described a read-only admin page and a registry keyed per app; both are gone.

## 1. Overview

mcp-service hosts tools and skills for every application and agent in the domain. It has
two faces over one registry, and a console over both:

| Face | Who | What |
|---|---|---|
| MCP, `/mcp/{app}/` | MCP clients (Cortex's Tutor app, agent_runtime, Claude Code, Claude Desktop) | `tools/*`, `prompts/*`, `resources/*`, scoped to the app in the path |
| REST | applications (Cortex, job2cool, the SDLC wall) and the console | CRUD, invoke, manifest, keys, activity, history |
| Console, `/admin` | people: the platform owner, app developers, auditors | one page over everything |

The implementations never leave the service: a tool record names a function in
`app/toolimpl*.py`; the registry holds data only.

## 2. Module map

| Module | Role |
|---|---|
| `app/main.py` | FastAPI app, the REST face, the MCP mount, the lifespan |
| `app/mcpserver.py` | the MCP server: tools with annotations and output schemas, prompts with arguments, `skill://` resources; app, caller and person from context variables |
| `app/mount.py` | the Streamable-HTTP mount at `/mcp`; parses the app from the path and the caller from the headers; refuses a foreign key or a missing one before the session manager runs |
| `app/invoke.py` | the one invocation pipeline both faces use: authorise → validate → run → record |
| `app/auth.py` | caller resolution (proxy-signed-in person, admin token, app key, anonymous) and the tier rules |
| `app/keys.py` | app keys: create (shown once), list, revoke, verify; fingerprints in `keys.json` |
| `app/validation.py` | JSON Schema 2020-12 validation of arguments and of schemas being saved |
| `app/activity.py` | the invocation record in SQLite: record, query, summary, CSV, retention |
| `app/registry.py` | the registry (schema v2), seeds, history, restore, migration from v1 |
| `app/admin.py` | the console's data endpoints: registry, health, attention, export |
| `app/console_page.py` | the console page (inline CSS and JS, no build step): Cortex's shell, menu bar, profile, status bar, the Help viewer |
| `app/identity.py` | the signed-in person's name and photo from Microsoft Graph with the proxy's access token; the sign-out hint |
| `app/oauth.py` | OAuth 2.1: the authorization server (RFC 8414 metadata, RFC 7591 registration, the code flow with PKCE behind the proxy's sign-in, JWT access tokens, rotating refresh tokens, revocation) and the RFC 9728 resource metadata |
| `app/help/` | the User Manual (English, and Portuguese in `manual/pt/`) and the Integration Guide (Markdown, README.md = contents, figures in `img/`) |
| `app/static/` | Cortex's vendored marked and DOMPurify; the self-hosted Inter and its licence; `pt.js`, the interface's Portuguese dictionary |
| `app/toolimpl.py`, `toolimpl_sdlc.py`, `toolimpl_nginx.py` | the shipped implementations |
| `tests/` | pytest suite, run inside the image by `docker build --target test .` |

### Data model (`data/registry.json`, version 2)

```json
{"version": 2,
 "tools":  {"web_search": {"name": "web_search", "apps": ["job2cool", "tutor"], "impl": "web_search",
            "tier": "read", "destructive": false, "idempotent": false, "enabled": true,
            "input_schema": {...}, "output_schema": null, "config": {}, "version": 1, ...}},
 "skills": {"cite_with_tag": {"name": "cite_with_tag", "apps": ["slides", "tutor"], "content": "...",
            "arguments": [{"name": "kb_tool", "required": false}], "tools": [...], "tags": [...],
            "enabled": true, "version": 1, ...}}}
```

A record is keyed by its name and offered to the apps in `apps`. `config.execution:
"client"` marks a tool the app's own page executes; the service only serves its schema and
refuses to run it. Writes append the new state to `data/history.json`; `restore` makes a
past version current as a new version. A version-1 registry (keyed `app/name`) is
migrated on first load: identical duplicates merge, differing ones are renamed
`name__app` and listed in `data/migration_report.json`.

### Per-app scoping

`/mcp/{app}/` and `?app=` filter to the records offered to that app. The un-scoped
endpoint lists everything enabled.

## 3. Request flows

**Invoke (both faces).** `mount.py` (MCP) or `main.tool_invoke` (REST) resolves the
caller from `Authorization` (admin token → `console`; `mcpk_…` → the key's id; nothing →
`anonymous`; an unknown key → 401) and the person from `X-On-Behalf-Of`. `invoke.run`
then: refuses a key for another app (403), refuses anonymous write-tier calls and, with
`MCP_REQUIRE_KEYS=1`, anonymous read-tier calls (401); refuses disabled and
client-executed tools (409); validates the arguments against `input_schema` (422, with
the JSON pointer of the failing property); runs the implementation (502 on failure);
records the call either way. MCP callers get the same code and message as an `isError`
result; a tool with an `output_schema` also returns `structuredContent`.

**Prompts and resources.** `prompts/list` advertises a skill's arguments; `prompts/get`
substitutes `{{name}}` placeholders (required ones must be given); `resources/read
skill://name` returns the content as written, `text/markdown`.

**Console.** The page loads `admin/registry` (records with last-used and 24 h counts),
`admin/health` and `admin/attention`; writes go to the REST endpoints with the admin
token the operator pastes (session storage only), and every save shows a diff first.

## 4. The Console

Six views: Overview (tiles, needs-attention list, recent calls), Tools (table, detail
drawer with Overview, Schema, Try it, Connect, Activity, History, Edit), Skills (same,
with a render-as-`prompts/get` Try it), Apps (endpoint, keys, offered counts, Connect
snippets), Activity (filters, summary, paging, CSV), Settings (implementations and what
binds to them, backends, auth mode, export, import with a dry run). Light and dark with
the Banco CTT tokens; a top strip and a full-width sheet at phone width.

Published on the domain by the service's own `nginx_register_app` tool at
`/mcp-console/` behind oauth2-proxy, owner only. On the internal network the page and
the reads are open; writes need the token.

## 5. Delivered and open

Delivered (2026-10-10): app keys and tier rules; the invocation record and its
endpoints; validation; shared tools and the v1 migration; history and restore; MCP
annotations, output schemas, prompt arguments, resources; the skills model and three
starter skills; the console; the test suite; the public path; job2cool's duplicate views
replaced by a link; Cortex sends its key and the learner's address.

Open: on-behalf-of token verification (after Cortex's Entra setup is in production);
`POST /skills/match` through the embeddings reranker, if a consumer ever wants automatic
skill selection; a per-app description override for a shared tool, if a real need appears.

## 6. Deployment

- **Container** — `python:3.12-slim`, `uvicorn app.main:app` on `:8080`, published to
  host `:4950`. Stages: `base`, `test` (runs pytest), `app` (the default).
- **Persistence** — `./data` holds `registry.json` (git-tracked), `history.json`,
  `keys.json`, `activity.db`, `migration_report.json`.
- **Networks** — see README.
- **Config (env)** — `MCP_DATA_DIR`, `MCP_ADMIN_TOKEN`, `MCP_REQUIRE_KEYS`,
  `MCP_RECORD_ARGS`, `MCP_RETENTION_DAYS`, `WEBSEARCH_URL`, `NEWSAPI_KEY`, `JENKINS_URL`,
  `PROXY_CONF_DIR`, `PROXY_CONTAINER`, the `SDLC_*` mounts.

## 7. Security model

- **No code from the UI.** The registry is data; the only executable surface is
  `toolimpl.IMPLS`, shipped with the service.
- **Sign-in is the proxy's** (Microsoft Entra ID through oauth2-proxy-entra), as for Cortex and
  Slides; MCP clients in a person's hands get OAuth 2.1 tokens through the same sign-in (`app/oauth.py`). The service trusts `X-Auth-Request-Email` only with `X-Mcp-Proxy-Secret`
  (`MCP_PROXY_SECRET`); administrators are `MCP_ADMIN_EMAILS`.
- **Writes are gated** by the signed-in administrator or the bearer token (`MCP_ADMIN_TOKEN`);
  the console keeps a pasted token in session storage and never in the page or the URL.
- **Write-tier tools are never anonymous**; read-tier tools stop being anonymous with
  `MCP_REQUIRE_KEYS=1`, and never are on the public path. A key is bound to one app and refused elsewhere; an OAuth
  token acts within its scopes for its person. A retired app answers nobody.
- **Keys and the token are stored as fingerprints**; a key is shown once.
- **Arguments are recorded as digests**; the JSON itself only for read-tier tools with
  `MCP_RECORD_ARGS=1`, never for write-tier tools.
- **`X-On-Behalf-Of` is recorded as declared** by the application, not verified.
- **Network isolation.** `websearch_server` is reachable only over `mcp_internal`.
- **The public path** is administrator-only behind oauth2-proxy-entra.
