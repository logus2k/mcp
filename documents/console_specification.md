# mcp-service — Platform and Console Specification

**Status:** implemented, 2026-10-10 (all phases of section 8; see "Decisions taken" at the end). Written from the code in `app/`, the live container
(`mcp-service:0.1.0`, started 2026-10-06) and the consumers in `~/env/assets`
(Cortex, Slides, job2cool, agent_runtime, the SDLC wall). Every statement about the
current state below was checked against the running service on the date above.

Companion files: [technical_architecture.md](technical_architecture.md) (describes
the service as it was before the admin page gained write surfaces; §4 and §5 are
out of date and are superseded by this document), [implementation_plan.md](implementation_plan.md)
(phases 1 to 5 delivered; phase 6 absorbed here), and the HTML mockup
[console_mockup.html](console_mockup.html).

---

## 1. Purpose

mcp-service is the domain's shared **tool and skill host**. It has two faces: a
standard MCP endpoint any client can connect to, and a management REST face that
authors the catalog. This document specifies:

1. the **platform changes** the service needs to be a governed capability rather
   than an internal utility: caller identity, an invocation record, validation,
   shared tools, record history, and the newer MCP features;
2. the **skills catalog**: what a skill is here, why it exists, and its model;
3. the **Console**: one browser frontend over both catalogs, replacing the two
   partial UIs that exist today (`/admin` in this project and the Skills/Tools
   views in job2cool).

### Audience
Platform owner (operates the service), application and agent developers (connect
to it), auditors (ask what left the network and on whose behalf).

### Non-goals
- Moving application-bound tools into this service. Cortex's tutor tools act on
  the student's screen; Slides' editing tools act on a draft deck under a lease.
  Those stay in their applications. This service hosts tools that are
  app-independent or that leave the network.
- Authoring executable code from the UI. Implementations stay in `app/toolimpl*.py`.
- Replacing Cortex's Developer SDK. Cortex's knowledge base is exposed by Cortex
  under its own keys; see §4.9 for how the two relate.

---

## 2. Current state (verified 2026-10-10)

| Area | State |
|---|---|
| MCP face | `/mcp/{app}/`, streamable HTTP, stateless, JSON responses. `initialize` reports protocol 2025-06-18 with `tools`, `prompts` and an `experimental.registry` capability. `tools/list`, `tools/call`, `prompts/list`, `prompts/get` work (a live `tools/call` of `fetch_url` returned page text). |
| REST face | `GET/PUT/PATCH/DELETE /tools[/{name}]`, `POST /tools/{name}/invoke`, `GET /tools/manifest`, the same for `/skills` minus invoke, `/health`, `/backends/health`, `/admin/*`. |
| Registry | One JSON file, `data/registry.json`, re-read on every request, written atomically. Records keyed `app/name`. 21 tools in 5 apps (agent_runtime 2, factory 1, job2cool 2, sdlc 5, tutor 11). 0 skills. |
| Implementations | 9: `web_search` (via the isolated Camoufox service), `fetch_url`, `newsapi_search`, five SDLC maturity tools, `nginx_register_app` (writes the domain proxy's conf, has the Docker socket). |
| Client-executed entries | 11 tutor tools carry `config.execution: "client"`; the server only serves their schema. |
| Auth | `MCP_ADMIN_TOKEN` bearer on PUT/PATCH/DELETE. **Invoke and MCP calls carry no identity and are not gated**, including the write-tier `nginx_register_app`. The service is on four networks (cortex-kb, mcp_internal, ci-network, logus2k_network, plus noted-network locally). |
| Admin page | Delivered well beyond the "read-only" the architecture document describes: health dots, per-app tabs, filter, enabled-only, dark mode, create/edit/delete for tools and skills, enable toggles, Try it, export, admin-token field. No activity, no history, no keys. |
| Second UI | job2cool's `frontend/js2c/mcp.js` is a full Skills/Tools admin over a backend proxy that injects the admin token and the `job2cool` scope. |
| Consumers | Cortex (`web_search` only, app `tutor`, by REST invoke). agent_runtime and the SDLC wall (by registry). Tutor (fetches its catalog). Slides: none. Claude Code / Desktop: none yet. |
| Known drift | The registry's 11 tutor entries are a stale copy of what Cortex's browser hardcodes (one name differs, four tools exist only in the browser). Nothing in Cortex reads them. |
| Tests | No tests directory in the repository. |

---

## 3. Goals

1. **Every call is attributable.** Who called which tool, for which app, on whose
   behalf, when, with what outcome. This is the gap Cortex's IAM assessment and
   accountability plan both name.
2. **Write-tier tools cannot be invoked anonymously.**
3. **One catalog, one console.** A tool or skill is defined once, offered to the
   apps that need it, and administered in one place.
4. **Connectable in a minute.** A developer or an MCP client gets a working
   connection from the Console without reading this service's code.
5. **Skills exist for a reason.** The skills catalog holds cross-cutting
   instructions several consumers must apply identically, and MCP clients can use
   them without integration work.

---

## 4. Platform changes

### 4.1 Caller identity: app keys

- **App key**: `mcpk_` + 43 URL-safe characters, bound to exactly one app. Shown
  once at creation, stored as a SHA-256 fingerprint in `data/keys.json`
  (`{id, app, name, fingerprint, created_at, expires_at, last_used_at, revoked_at}`).
  Created, listed and revoked through the Console's Apps view (admin bearer).
  At most 20 active keys per app.
- **Where it is sent**: `Authorization: Bearer mcpk_…` on `POST /tools/{name}/invoke`
  and on every request to `/mcp/{app}/`. A key for app A used on `/mcp/B/` is
  refused (`403`). The console's Try it sends the admin bearer instead, and is
  recorded as caller `console`.
- **On behalf of**: an optional `X-On-Behalf-Of: <email>` names the person the
  application is acting for. It is recorded, never verified here; this mirrors
  Cortex's service-key convention, so Cortex forwards the learner's address when
  it calls `web_search`. Verification by on-behalf-of token is a later step, after
  Cortex's own `CORTEX_OBO_*` setup is in production.
- **Enforcement**:
  - write-tier tools: a valid app key is **always** required;
  - read-tier tools: required when `MCP_REQUIRE_KEYS=1` (production), optional
    otherwise, so existing callers keep working during the roll-out. Calls without
    a key are recorded with caller `anonymous` and surfaced in the Console as a
    warning while the flag is off.
- **Transport note**: streamable HTTP carries the header on every POST, so the
  stateless session manager needs no change; the check happens in `mount.py`
  before `handle_request`.

### 4.2 Invocation record

- **Store**: SQLite at `data/activity.db` (WAL mode). One table:

  ```
  calls(id TEXT PK, ts TEXT, app TEXT, tool TEXT, transport TEXT,   -- rest | mcp | console
        caller TEXT,             -- key id | console | anonymous
        on_behalf_of TEXT,       -- email or ''
        ok INTEGER, error TEXT,  -- error: the {type}: {message} the caller received
        duration_ms INTEGER, args_digest TEXT, args_json TEXT, result_chars INTEGER)
  ```
  `args_json` is kept only for read-tier tools and only when
  `MCP_RECORD_ARGS=1`; otherwise `args_digest` (SHA-256 of the canonical JSON)
  is enough to correlate. Retention: 90 days, pruned daily.
- **Endpoints** (reads open on the internal network, like the rest):
  - `GET /activity?app=&tool=&caller=&ok=&since=&until=&limit=&cursor=` — newest first.
  - `GET /activity/summary?window=24h|7d|30d&app=` — per tool: calls, errors,
    p50 and p95 duration, last used.
- **What it unlocks**: the Console's Activity view, last-used and calls columns
  in the catalog, the "never called" hygiene warning, and an audit answer to
  "what left the network for this person last week".

### 4.3 Argument validation

Validate `args` against the record's `input_schema` (JSON Schema 2020-12) on
both faces before dispatch. On failure return
`{"error": {"code": "invalid_arguments", "message": "...", "path": "/max_results"}}`
with `422` (REST) or an `isError` tool result (MCP). Adds `jsonschema` to
`requirements.txt`; Slides already pins the same library.

### 4.4 Shared tools

Replace `app: str` on a tool record with `apps: [str]`. A record is keyed by
`name` alone; it is offered on `/mcp/{app}/` and `/tools?app=` for every app in
its list. Migration (one-off script, `scripts/migrate_shared.py`):
- records with the same name, `impl`, `input_schema` and `config` are merged and
  their app lists united (today: `web_search` in job2cool and tutor; `fetch_url`
  in job2cool and agent_runtime);
- records with the same name but different content are renamed `name__app` and
  listed in the migration report for a human decision.

### 4.5 Record history

Every `PUT`, `PATCH` and `DELETE` appends the previous version to
`data/history.json` as `{kind, name, version, ts, actor, record}`. `actor` is
`console` plus the first 8 characters of the admin token's fingerprint, or the
app key id for programmatic writes. `GET /tools/{name}/history` and
`GET /skills/{name}/history` return the list; the Console shows a diff between
any two versions and offers **Restore**.

### 4.6 MCP features to adopt

- **Tool annotations**: `tier: read` → `readOnlyHint: true`; `tier: write` →
  `readOnlyHint: false`, `destructiveHint` from a new boolean field `destructive`
  (default `false`; `nginx_register_app` with `unregister` is the first `true`),
  `idempotentHint` from `idempotent` (default `false`).
- **Output schema**: optional `output_schema` on a record, served as
  `outputSchema` and used to return `structuredContent` beside the text.
- **Resources**: each enabled skill is also served as a resource
  `skill://{name}` with `text/markdown` content, so clients that load skills as
  files (Claude Code's skill loader reads `SKILL.md`-shaped text) can use them.
- **Prompt arguments**: `prompts/list` advertises a skill's `arguments`;
  `prompts/get` substitutes `{{name}}` placeholders in the content.

### 4.7 Skills model

A skill is a **reusable instruction** a model should follow, owned centrally,
versioned, and offered to the apps that need it.

```json
{
  "name": "cite_with_tag",
  "display_name": "Cite knowledge-base passages with their tag",
  "description": "How to cite a passage returned by a knowledge-base tool so the page can turn it into a button.",
  "content": "When you use a passage returned by {{kb_tool}}, cite it inline with its tag exactly as returned ...",
  "arguments": [{"name": "kb_tool", "description": "the search tool's name", "required": false}],
  "apps": ["tutor", "slides"],
  "tools": ["search_knowledge_base", "kb_search"],
  "tags": ["citation", "knowledge-base"],
  "enabled": true,
  "version": 3,
  "created_at": "...", "updated_at": "..."
}
```

Changes from today's model:
- `triggers` and `priority` are **removed**. No consumer performs trigger-based
  injection, and string triggers are the wrong instrument for "does this request
  need this skill". If a consumer wants automatic selection, it is a later
  endpoint `POST /skills/match` backed by the embeddings service's reranker,
  never by string rules.
- `apps` (shared, as for tools), `tools` (the tools the skill expects, shown as
  links in the Console and used to warn when a skill names a tool its app is not
  offered), `tags`, `arguments`, `version`.

**Why a skills catalog, concretely.** Cortex and Slides keep their system prompts
in their own repositories, tuned per model with measurements; those stay there.
What the catalog is for is instruction that several consumers must apply the same
way and that someone must be able to change in one place:
- the citation-tag convention (`[markdown_chunk:<hex>]`) that both Cortex and
  Slides enforce;
- the European Portuguese rule;
- the "answers are AI-generated" disclosure the accountability plan requires;
- the request-handling rules that agent_runtime agents share.
Two payoffs exist on day one: any MCP client, Claude Code included, surfaces
`prompts/list` as invokable commands; and each instruction gets an owner, a
version, an enabled flag and a history, which a prompt file in each repository
does not have.

### 4.8 Consolidation

- job2cool's Skills/Tools views are replaced by a link to the Console, scoped to
  job2cool (`/admin#app=job2cool`). Its backend proxy stays for programmatic use
  only. One UI, one place to fix things.
- The Console is served at `/admin` as today and published on the domain proxy
  behind oauth2-proxy at `/mcp-console/` with `admin_only`, using the service's
  own `nginx_register_app` tool. Reads inside the network stay open; the public
  path is for people.

### 4.10 Sign-in: Microsoft Entra ID through the domain proxy

As Cortex and Slides: authentication is not an application feature. The console's
public path `/mcp-console/` is gated by oauth2-proxy-entra (`auth_request
/oauth2-entra/auth-admin`, the administrator's allow-list in `route-entra.conf`), which
forwards the person as `X-Auth-Request-Email`. The service trusts that header only when
`X-Mcp-Proxy-Secret` matches `MCP_PROXY_SECRET` (set in `mcp/.env` and sent by
`proxy_server/conf/secrets/mcp-console.conf`, both git-ignored), so nothing on the
internal network can name a person. A signed-in person on `MCP_ADMIN_EMAILS` (or anyone
the proxy admitted, when the list is empty) is an **administrator**: writes, keys and
Try it work without a pasted token and are recorded by their address; a signed-in
person not on the list may read and use read-tier tools. `GET /admin/me` tells the page
who it runs as; the page then hides the token field and shows the person and the
proxy's sign-out. The admin token remains for programmatic writes and for the page on
the internal port.

### 4.9 Registry hygiene

- Remove the 10 tutor entries that no consumer reads (keep `web_search`), or make
  Cortex's Learning Assistant fetch its catalog from `/tools/manifest?app=tutor`.
  The second is preferable only if Cortex also moves its per-role filtering into
  record metadata (`roles: [instructor, coach, mentor]`); otherwise delete.
- Update `technical_architecture.md` §4 and §5 to the delivered state and link here.
- Add `tests/` with: registry round-trip, validation errors, key enforcement
  per tier, an end-to-end MCP `initialize` → `tools/list` → `tools/call` against
  a test app with a stub implementation.
- Cortex's knowledge base is **not** proxied here. When Cortex mounts its own MCP
  face over its v1 API (under its own keys), the Console's Apps view links to it
  as an external server so a developer sees both from one place.

---

## 5. The Console

### 5.1 Principles

- **Self-contained**: one HTML page served by `admin.py`, inline CSS and JS, no
  build step, no new Python dependencies (the project's convention).
- **The domain's look**: the Banco CTT tokens Cortex and Slides use
  (`tokens.css`: Inter, the red primary, the slate neutrals, 4/8/12/16 spacing),
  light and dark, `data-theme` plus OS preference.
- **Scanned, not read**: summary before detail; state encoded in form (pill,
  dot, stripe) as well as in words; every number says where it came from.
- **Works at phone width** (navigation becomes a top strip, the detail drawer
  becomes a full-width sheet). Keyboard: `/` focuses search, `Esc` closes the
  drawer, `j`/`k` move the row selection.
- **Writes are deliberate**: the admin token lives in session storage only; every
  write shows a diff of the record before **Save**; delete and write-tier Try it
  need an in-page confirmation (the viewer has no dialogs).

### 5.2 Information architecture

| View | Who | Job |
|---|---|---|
| **Overview** | everyone | Is the platform healthy, what needs attention, what happened recently. |
| **Tools** | owner, developer | Find a tool, read its schema, try it, connect to it, change it. |
| **Skills** | owner, developer | Same for instructions: read, edit with preview, try `prompts/get`, see which tools it expects. |
| **Apps** | owner, developer | An app's capability surface: endpoint, keys, the tools and skills it is offered, its calls. |
| **Activity** | auditor, owner | The invocation record with filters and export. |
| **Settings** | owner | Implementations and what binds to them, backends, auth mode, export and import. |

Deep links use a bare hash token (`#tools`, `#tool-web_search`, `#app-tutor`),
nothing else in the URL.

### 5.3 Overview

- **Header**: service and backend health dots (service, websearch_server,
  Jenkins over ci-network), auth mode (`keys required` / `keys optional` /
  `open`), theme toggle, token field.
- **Tiles**: tools (enabled/total), skills, apps, calls in 24 h with error rate.
  Each tile links to its view; the calls tile names the window.
- **Needs attention** (computed server-side, `GET /admin/attention`):
  - tools never called in 90 days (needs §4.2);
  - duplicate records (same name, same content, several apps; disappears after §4.4);
  - write-tier tools reachable without a key (disappears after §4.1);
  - orphan records (impl not in `IMPLS`) and unused implementations (already computed today);
  - skills that name a tool their apps are not offered.
- **Recent activity**: the last 10 calls, linking to Activity.

### 5.4 Tools

- **Toolbar**: search (name, description, impl, app), app chips, tier chips,
  enabled-only, **New tool**.
- **Table columns**: name, apps, tier, execution (server/client), impl, last
  used, calls 24 h, enabled toggle. Sorting on name, last used, calls.
- **Row select** opens the **detail drawer** (right, 520 px; full width on phone)
  with tabs:
  1. **Overview**: description, apps offered, endpoint per app, implementation
     and its backend health, created/updated, enabled toggle, Edit, Delete.
  2. **Schema**: the input schema rendered as a property table (name, type,
     required, default, description) with a raw JSON toggle; output schema if any.
  3. **Try it**: a form generated from the schema (strings, integers with
     min/max, booleans, enums as selects, free JSON for objects), **Run**,
     result pane with duration and a **Copy as curl** of exactly what ran.
     Write-tier: an in-page confirmation strip naming the tool and the app.
  4. **Connect**: copyable snippets for this tool's app: curl (REST invoke),
     Python (`httpx`), Claude Code (`claude mcp add --transport http <app> <url>`),
     Claude Desktop (`mcpServers` JSON), generic MCP client config. The app key
     placeholder is filled when the viewer pastes one into the token field.
  5. **Activity**: the last 50 calls of this tool with filters, linking to the
     full view.
  6. **History**: versions with diff and Restore.
- **Editor** (New / Edit): a drawer form, not a modal: name (readonly when
  editing), display name, description, apps (multi-select from known apps, free
  text to add), tier, destructive, idempotent, execution, impl (select from
  `IMPLS`, disabled when execution is client), input schema (JSON editor with
  validation and a property-table preview), config (JSON), enabled. **Save**
  shows the diff against the current record first.

### 5.5 Skills

- **Table**: name, apps, tags, tools expected, version, updated, enabled.
- **Drawer tabs**: Overview, **Content** (Markdown editor left, rendered preview
  right; on phone, tabs), Arguments (table), **Try it** (fill arguments, see the
  exact `prompts/get` result), Connect (the same snippets, plus "as a resource":
  `skill://name`), Activity (prompt fetches, once §4.2 records them), History.
- **Empty state**: the catalog starts empty; the view explains in two sentences
  what belongs here and what does not (app-tuned system prompts stay in the
  app), and offers **New skill** with three starter templates named above.

### 5.6 Apps

One card per app, expandable:
- endpoint `/mcp/{app}/` and REST base, with the Connect snippets;
- **Keys**: list (name, created, expires, last used), **New key** (shown once
  with a copy button and an expiry), Revoke with in-page confirmation;
- tools offered (count, link to Tools filtered), skills offered;
- calls in 24 h, errors, top tools;
- **External servers** (§4.9): a link list, starting with Cortex's MCP face when
  it exists, so an app developer sees everything they can connect to.

### 5.7 Activity

- Filters: window (24 h, 7 d, 30 d, custom), app, tool, caller, on-behalf-of,
  status, transport. Free text over error messages.
- Table: time, app, tool, caller, on behalf of, transport, duration, status
  (ok / error with the message on hover and on expand).
- Export CSV of the current filter (served by `GET /activity.csv`, since the
  viewer sandbox blocks page-started downloads when published as an artifact;
  inside the real console a normal link works).
- Summary strip above the table: calls, error rate, p95, top three tools.

### 5.8 Settings

- **Implementations**: the 9 functions, each with the records bound to it and
  the backend it depends on; orphans and unused implementations flagged.
- **Backends**: websearch_server, NewsAPI (configured / not), Jenkins, the proxy
  conf mount, the SDLC mounts; probe results with timestamps.
- **Auth**: mode, whether the admin token is set, `MCP_REQUIRE_KEYS`,
  `MCP_RECORD_ARGS`, retention.
- **Export / Import**: registry JSON (all or per app), activity CSV; import with
  a dry-run diff.

### 5.9 States and copy

- Empty catalogs, empty activity, a backend down, a token missing when a write
  is attempted, a key refused: each has a designed state that names the cause
  and the next action, in the same words as the API's error.
- Buttons say what happens: **Run**, **Save**, **Revoke key**, **Restore
  version 2**. Toasts confirm in the past tense.

---

## 6. API additions (summary)

| Method and path | Auth | Purpose |
|---|---|---|
| `POST /apps/{app}/keys` | admin | create a key (returns it once) |
| `GET /apps/{app}/keys` | open | list keys (fingerprints, never the key) |
| `DELETE /apps/{app}/keys/{id}` | admin | revoke |
| `GET /apps` | open | apps with counts, endpoints, key counts |
| `GET /activity`, `GET /activity/summary`, `GET /activity.csv` | open | §4.2 |
| `GET /tools/{name}/history`, `GET /skills/{name}/history` | open | §4.5 |
| `POST /tools/{name}/restore` `{version}` | admin | restore a version |
| `GET /admin/attention` | open | the Overview's warnings |
| `POST /tools/{name}/invoke` | app key per §4.1 | unchanged shape, now validated and recorded |
| `/mcp/{app}/` | app key per §4.1 | unchanged, plus annotations, resources, prompt arguments |

Records gain: `apps` (replaces `app`), `destructive`, `idempotent`,
`output_schema`, `version`. Skills gain `arguments`, `tools`, `tags`, `apps`,
`version` and lose `triggers`, `priority`.

---

## 7. Security

- Keys and the admin token are stored as fingerprints; the Console keeps the
  token in session storage and never in the page source or the URL.
- The Console is read-open inside the network and admin-only on the public path.
- Write-tier tools are never anonymous. `nginx_register_app` additionally keeps
  its own validation and rollback.
- Recorded arguments are off by default and never recorded for write-tier tools.
- `X-On-Behalf-Of` is recorded as received; the Console shows it with a
  "declared by the application" marker until token verification exists.
- No executable content enters through the UI; schemas and skill content are data.

---

## 8. Delivery

| Phase | Scope | Acceptance |
|---|---|---|
| **0 Hygiene** | §4.9 docs, tutor entries, `tests/` skeleton. | Architecture doc matches the page; `pytest` runs the MCP end-to-end test green in the container. |
| **1 Record and validate** | §4.2, §4.3, Activity view, last-used columns, attention list. | A call from Cortex appears in Activity within a second with app, tool, duration and outcome; an invalid argument returns `422` with the path. |
| **2 Keys** | §4.1, Apps view with key management, Connect snippets. | A write-tier invoke without a key is refused; Cortex calls `web_search` with its key and the learner's address, both visible in Activity. |
| **3 Shared tools and history** | §4.4, §4.5, Tool drawer redesign, editor with diff. | One `web_search` record offered to two apps; a restored version is served by `tools/list`. |
| **4 Skills** | §4.6 resources and prompt arguments, §4.7 model, Skills view, the three starter skills. | Claude Code lists the three skills as prompts; `prompts/get` substitutes arguments; Slides and Cortex each pull `cite_with_tag` once. |
| **5 Consolidation** | §4.8, public path, job2cool link. | job2cool's views are gone; the Console opens behind oauth2-proxy at `/mcp-console/` for the owner only. |

Each phase ships on its own, in order, and the docs are updated with it.

---

## 9. Open questions

1. **Who verifies the person** for an autonomous agent with nobody behind it?
   Neither this service nor Cortex has an answer. Until there is one, such
   callers get a key with `on_behalf_of` empty, and the Activity view shows them
   as "application only".
2. **Per-app description overrides** for a shared tool (the tutor's `web_search`
   description differs in one sentence from job2cool's). The proposal is one
   description per record; if a real need appears, add `overrides: {app: {description}}`.
3. **Where Cortex's MCP face lives**: inside Cortex over v1 (recommended in the
   discussion of 2026-10-10) or as forwarding tools here. The Console design
   supports either through the external-servers list.

---

## 10. Decisions taken during implementation (2026-10-10)

- **Migration outcome.** `web_search` (job2cool, tutor) merged into one record. `fetch_url`
  differed between agent_runtime (documented schema) and job2cool (bare schema): the
  documented record is now offered to both and the renamed copy was deleted. The history
  records both steps.
- **Tutor entries kept.** The 10 client-executed tutor records stay: the Tutor application
  (`~/env/assets/tutor`) fetches its catalog from `/tools?app=tutor`. The "never called"
  warning excludes client-executed tools, since the service never runs them.
- **Starter skills seeded** on first load of an empty skills catalog (`cite_with_tag`,
  `pt_pt_style`, `ai_generated_disclosure`), offered to the apps named in section 4.7.
  `slides` therefore appears as an app with skills and no tools.
- **`sdlc_advise` is tier `write`** in the registry as found; not changed here.
- **Console transport details.** The admin token lives in session storage; the theme
  choice in local storage. Try it runs as the console (admin token) and is recorded as
  caller `console`. Deep links: `#tools`, `#tool-<name>`, `#skill-<name>`, `#app=<app>`.
- **Public path** `/mcp-console/` → host port 4950, hand-written `route-mcp-console.conf`
  modelled on the Slides route, gated by Microsoft Entra ID (`/oauth2-entra/auth-admin`,
  section 4.10). It was first registered with the Google owner gate by the service's own
  tool and replaced the same day. The REST face is reachable under the same prefix, under
  the same gate.
- **Cortex** sends `Authorization: Bearer <CORTEX_MCP_KEY>` and `X-On-Behalf-Of: <learner>`
  on its `web_search` call; the key (app `tutor`, name `cortex-learning`, 365 days) is in
  Cortex's `.env`. **job2cool**'s Skills and Tools views list what the app is offered and
  link to the console; its backend proxy is unchanged.
- **Keys remain optional** (`MCP_REQUIRE_KEYS=0`) until agent_runtime, job2cool and the
  SDLC wall have keys. The Overview lists the apps without one.
- **No regular expressions** were added to the service or the console; text matching is
  done with string operations, per the workspace rule.

## 11. The shell, Help and the manuals (2026-10-10, later the same day)

- **The shell is Cortex's and Slides'**: the 200px side menu with the Banco CTT wordmark and "MCP SERVER" spread to
  the logo's width, sections with Caption titles, 48px items with 24px outline icons (stroke 1.6) in currentColor,
  the view on screen in brand red with no background, Settings at the bottom with its pull-down (theme, Settings),
  the 32px collapse button and the 72px rail (remembered), the tablet's overlay menu, the phone's bottom bar and
  header; the 72px top bar with Cortex's **menu bar** (Catalog, Apps, Activity, View, Monitoring, Help; Alt+letter
  opens a menu) and the **profile** at the right (photo or initials, name, chevron; menu with theme and Sign out);
  the 28px **status bar** (service pill, view with the focus and its details, then the backends, the keys mode,
  the record and the connection). The self-hosted Inter and the logos are Cortex's own files, copied.
- **Backend monitoring** moved from a row of indicators (it would not scale) to the Monitoring menu, the status
  bar's summary and Settings.
- **Name and photo** come from Microsoft Graph with the access token the proxy forwards (`app/identity.py`,
  Cortex's `_userinfo_of`); the ID token fills the sign-out hint. Without a token, the address's start and initials.
- **Help** opens the **User Manual** (`app/help/manual/`, 36 task pages in 7 chapters, figures captured from the
  console), the **Integration Guide** (`app/help/guide/`, 7 pages: the equivalent of Cortex's Developer SDK, since
  there is no library to install) and the **Technical Architecture** (`documents/`, served from a fixed list), in
  a Help view that reuses Cortex's viewer: Markdown through marked and DOMPurify (Cortex's vendored copies), the
  contents parsed from README.md beside the page, links opening in place, a Next link.
- **Portuguese** (done later the same day, as Cortex does it): the page is translated as it is built by Cortex's
  translator pattern (one dictionary `app/static/pt.js`, English → European Portuguese, exact strings and `{0}`
  templates, content areas excluded, no regular expressions), the language kept under `localStorage
  mcp.uiLanguage` and switched from the profile's menu and the Settings pull-down (`?lang=pt` in the address sets
  it too); the User Manual has a Portuguese edition (`app/help/manual/pt/`, the same 37 pages, the figures shared)
  opened when the interface is Portuguese. The Integration Guide stays English, as Cortex's Developer SDK does.

## 12. OAuth 2.1 for MCP clients (2026-10-11)

The service is the MCP **resource server** and hosts its own **authorization server** (`app/oauth.py`), as the MCP
specification (2025-06-18) prescribes for remote HTTP servers; the person's sign-in stays the domain proxy's
(Microsoft Entra ID), exactly as for the console.

- **Metadata**: RFC 8414 at `/.well-known/oauth-authorization-server`, RFC 9728 at
  `/.well-known/oauth-protected-resource` (also path-aware per app); both also at the domain root's path-aware
  forms (`/.well-known/…/mcp-console…`) through the proxy. A 401 on either face carries
  `WWW-Authenticate: Bearer resource_metadata="…"`.
- **Registration**: RFC 7591 at `/oauth/register`; public clients (PKCE) or `client_secret_post`; redirect URIs are
  `https://` or `http://localhost`. Registered clients are listed and removed in Settings › OAuth clients.
- **Authorization code with PKCE S256**: `/oauth/authorize` is behind the proxy's administrator gate (widen to the
  domain's accounts by pointing the location at `/oauth2-entra/auth-cortex` when wanted); a consent page names the
  client and the scopes; `/oauth/decision` records the answer and redirects with the code (10 min, single use).
- **Tokens**: `/oauth/token` issues HS256 JWTs (`sub` = the person, `client_id`, `scope`, `aud` = the MCP
  endpoint, 1 h) and rotating refresh tokens (30 days); `/oauth/revoke` ends one. The signing key lives in
  `data/oauth_signing.key` (or `MCP_OAUTH_SIGNING_KEY`); state in `data/oauth.json`.
- **Scopes**: `tools:read` (default), `tools:write` and `admin`; the last two act only for people on
  `MCP_ADMIN_EMAILS` when it is set. Calls are recorded as `oauth:<address>`, acting for that address.
- **The public path**: the proxy leaves `/mcp-console/oauth/*`, `/mcp-console/.well-known/*` and
  `/mcp-console/mcp/*` ungated and marks them `X-Mcp-Public: 1`; the service then never answers anonymously there,
  whatever `MCP_REQUIRE_KEYS` says. The console stays behind the sign-in.
- `MCP_PUBLIC_URL` (`https://logus2k.com/mcp-console`) is the issuer and the resource's address.
- Verified live on 2026-10-11: metadata at every address, the challenge on an anonymous call, public registration,
  the sign-in redirect, consent, a token exchanged at the public endpoint, MCP calls with it on the public endpoint,
  refresh rotation, revocation, the record under the person's address.

## 13. The application catalog (2026-10-11)

An app is now a **record** (`registry.json` → `apps`): name, display name, description, owner, contact, status
(`active` | `retired`), tags, versioned with history and restore like tools and skills.

- A tool or skill can be offered only to registered apps (`422 unknown app(s)` otherwise); a key can be issued only to
  a registered, active app.
- A **retired** app answers nobody: its MCP endpoint and REST invokes are refused with `403`, no key can be issued;
  its records, keys and history stay.
- Deleting an app in use is refused (`409`) unless forced; forced, it withdraws the app from every tool and skill and
  revokes its keys. A tool left offered to no app is flagged on the Overview.
- The apps that existed before the catalog were registered automatically on first load, with a description that
  says so; the Overview flags any name a record still uses without a registration.
- Endpoints: `GET /apps` (records merged with counts and keys, `registered` flag), `GET/PUT/DELETE /apps/{name}`,
  `GET /apps/{name}/history`, `POST /apps/{name}/restore`. The console's Apps view edits the records (New app, Edit,
  Register on an unregistered name); the tool and skill editors offer the registered apps as checkboxes.

### 12.1 The client credentials grant (2026-10-11, later)

A **machine client** is registered by an administrator for an app of the catalog (`POST /apps/{app}/clients`:
name, scopes among `tools:read` and `tools:write`; id `mcpm_…` and a secret shown once) and asks `/oauth/token`
with `grant_type=client_credentials`. The token (1 h, no refresh token) acts as the app: `sub` = `app:<name>`,
accepted on that app's endpoint only, write-tier tools with `tools:write`, never an administrator; a retired app's
clients get no token; removing the client (`DELETE /apps/{app}/clients/{id}`, or the forced delete of the app) ends
its tokens, since a token is valid only while its client exists. Dynamic registration refuses the grant. Calls are
recorded as `client:<id>`. Keys stay for programs that cannot run the exchange.
