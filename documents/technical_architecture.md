# mcp-service — Technical Architecture

Shared **tool + skill host** for the app fleet. A single service that exposes a
declarative registry over two faces, plus a read-only admin area for consulting
the catalog.

---

## 1. Overview

`mcp-service` is a FastAPI application that fronts a JSON-persisted registry of
**tools** (callable capabilities) and **skills** (reusable instruction
templates). It presents three faces:

| Face | Path | Purpose |
|------|------|---------|
| **Standard MCP** | `/mcp/` · `/mcp/{app}/` | Streamable-HTTP (official `mcp` SDK). Any MCP client gets `tools/list`, `tools/call`, `prompts/list`, `prompts/get`. Tools → MCP tools; skills → MCP prompts. The interoperable consumption surface. |
| **Management REST** | `/tools…` · `/skills…` | CRUD authoring + `POST /tools/{name}/invoke` + `GET /tools/manifest`. MCP is a consumption protocol, not an authoring one — so authoring lives here. |
| **Admin area** | `/admin` · `/admin/registry` | Read-only browser view over the whole registry (all apps). Consult-only; never authors. |

**Design tenets**
- **Declarative catalog, shipped implementations.** Tools are catalog entries
  (name, JSON-schema, which built-in `impl`, config, enabled flag). Executable
  code ships with the service in `app/toolimpl.py`; the UI/registry never
  authors or stores executable code. Secure by construction.
- **One concern per module.** `registry` (persistence), `toolimpl` (impls),
  `mcpserver` (MCP surface), `mount` (transport), `admin` (browser view),
  `main` (REST + wiring).
- **Reads open, writes gated.** On the internal network, reads and tool
  consumption are open; only `PUT`/`DELETE` require a bearer token
  (`MCP_ADMIN_TOKEN`). Empty token = open (dev).

---

## 2. Module map

```
app/
  main.py        FastAPI app: REST management face, health, wiring, admin router
  registry.py    JSON-persisted registry (tools + skills), per-app scoping, locking
  toolimpl.py    Built-in async implementations + IMPLS dispatch table
  mcpserver.py   Standard MCP server surface (list/call tools, list/get prompts)
  mount.py       Streamable-HTTP transport mounted at /mcp, per-app path scoping
  admin.py       Read-only admin area: /admin (HTML) + /admin/registry (JSON)
data/
  registry.json  Persisted catalog (git-tracked; the source of truth)
```

### Data model

**Tool** — `{ app, name, display_name, description, impl, tier, enabled,
input_schema, config, created_at, updated_at }`
- `impl` binds to a function key in `toolimpl.IMPLS`.
- `tier` ∈ `read` | `write` (advisory classification of side effects).
- `config.execution` ∈ `server` | `client` — server-executed tools run in the
  service; client-executed tools (e.g. tutor UI actions) are dispatched by the
  consuming app.
- `input_schema` is the JSON-schema advertised to MCP clients / LLMs.

**Skill** — `{ app, name, display_name, description, content, triggers,
priority, enabled, … }` — exposed over MCP as a **prompt**. Trigger-based
auto-injection is a consumer concern; MCP just serves the catalog + content.
*(The registry supports skills; none are registered yet.)*

### Per-app scoping

Records are keyed `{app}/{name}`. The MCP transport reads the app from the path
segment (`/mcp/{app}/`) into a `contextvars` var so `list/call` handlers filter
to that app; no segment = aggregate view. REST endpoints scope via `?app=`
(default `job2cool`).

---

## 3. Request flows

**MCP consumption** — client → `/mcp/{app}/` → `mount.mcp_asgi_app` pins
`current_app`, normalises path → `StreamableHTTPSessionManager` → `mcpserver`
handlers → `registry.list_tools(app)` (enabled only) / `toolimpl.invoke(impl,
args, config)`.

**REST invoke** — `POST /tools/{name}/invoke?app=` → registry lookup → reject if
disabled → `toolimpl.invoke(...)` → `{tool, result}`.

**Admin consult** — browser → `GET /admin` (self-contained HTML) → page fetches
`GET /admin/registry` → aggregate JSON across all apps → client-side render.

**web_search delegation** — `web_search` impl → `httpx` POST to the isolated
`websearch_server` (Camoufox stealth browser) over `mcp_internal`.

---

## 4. Admin area

A dependency-free, **read-only** browser view whose sole job is to *consult* the
catalog. Authoring deliberately stays on the CRUD REST face.

### Implementation
- **`GET /admin`** — one self-contained HTML page: inline CSS + vanilla JS, no
  templates, no static dir, no Jinja, no new dependencies.
- **`GET /admin/registry`** — aggregate JSON in a single read: `apps`, `tools`,
  `skills`, `tools_by_app`, `skills_by_app`, `impls`, and `counts`.

### Current capabilities (delivered)
- All apps in one view; per-app filter tabs.
- Live search over name / description / impl / app.
- "Enabled only" toggle.
- Tier and enabled badges; client-vs-server execution indicator.
- Click-to-expand `input_schema` and `config` per tool.
- Separate skills table (renders gracefully while empty).
- Summary counts (apps, enabled/total tools, enabled/total skills).

### Why reads stay open
Consistent with the rest of the REST read surface on the internal network. Only
writes are bearer-gated; a read-only consult view needs no token.

---

## 5. Capability roadmap

Prioritised by how far each goes beyond pure consulting.

### Read-only (low risk, natural next steps)
- **Backend health panel** — surface `/backends/health` (websearch_server) and
  `/health` (impls, admin_auth mode) at the top of the page with a live
  indicator.
- **Impl coverage view** — list `toolimpl.IMPLS` and flag any registered tool
  whose `impl` has no backing function (catches broken catalog entries).
- **Per-tool MCP/exec clarity** — show the serving endpoint (`/mcp/{app}/`) and
  client-vs-server execution per tool.
- **Export** — download the registry (or a per-app slice) as JSON for
  backup/diffing.

### Test / observe (medium)
- **"Try it" panel** — invoke a `read`-tier tool from the UI via
  `POST /tools/{name}/invoke` and show the result; gate `write`-tier behind a
  confirm.
- **Invocation log / metrics** — per-tool counts, last-used, error rates
  (requires a small usage store; none exists today).

### Authoring (higher — needs the bearer token + write UI)
- **Enable/disable toggle** — highest-value write: flip `enabled` without
  editing JSON (one `PUT`).
- **Create/edit tools & skills** — forms over the existing `PUT` endpoints,
  `impl` as a dropdown from `IMPLS`, JSON-schema validation. Also where **skill
  authoring** finally gets exercised.
- **Auth UX** — an admin-token field in the UI once writes are enabled
  (`MCP_ADMIN_TOKEN` already gates them).

**Recommended next two:** the **backend health panel** and the
**enable/disable toggle** — highest signal for the least surface area.

---

## 6. Deployment

- **Container** — `python:3.12-slim`, `uvicorn app.main:app` on `:8080`,
  published to host `:4950`.
- **Persistence** — `./data` volume holds `registry.json` (git-tracked).
- **Networks** — `noted-network` (apps reach mcp-service) and `mcp_internal`
  (mcp-service reaches the isolated `websearch_server`).
- **Config (env)** — `MCP_DATA_DIR`, `WEBSEARCH_URL`, `MCP_ADMIN_TOKEN`
  (writes), `NEWSAPI_KEY` (newsapi_search; env-only, never in the registry).

---

## 7. Security model

- **No code from the UI.** The registry is purely declarative; the only
  executable surface is `toolimpl.IMPLS`, shipped with the service.
- **Bearer-gated writes.** `PUT`/`DELETE` require `Authorization: Bearer
  <MCP_ADMIN_TOKEN>` when the token is set.
- **Secrets via env, not registry.** API keys (e.g. NewsAPI) resolve from
  `config` *or* environment, and are kept out of the git-tracked registry.
- **Network isolation.** `websearch_server` is reachable only over
  `mcp_internal`; other apps observe its liveness through
  `/backends/health` rather than direct access.
- **Admin area is read-only**, so it introduces no new write surface.
