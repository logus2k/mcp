# mcp-service — Implementation Plan

Turns the capability roadmap in [technical_architecture.md](technical_architecture.md)
§5 into concrete, sequenced, executable phases. Each phase is independently
shippable, lists the files it touches, and has explicit acceptance criteria.

**Conventions**
- No new Python dependencies — keep the admin area self-contained (inline HTML/JS).
- Reads stay open; any write surface is bearer-gated via `MCP_ADMIN_TOKEN`.
- The registry stays declarative — no executable code enters via the UI.
- After each phase: `py_compile` the changed modules + validate the data shape
  against the live `registry.json`; full stack runs in Docker (`compose up --build`).

---

## Phase 1 — Backend health panel + impl coverage (read-only)

**Goal:** Surface service/backend liveness and catch broken catalog entries,
directly in `/admin`.

**Changes**
- `app/admin.py`
  - Extend `GET /admin/registry` payload with:
    - `impls` already present; add `orphans` — registered tools whose `impl` is
      not in `toolimpl.IMPLS`.
    - `unused_impls` — impls with no tool bound to them (informational).
  - Add `GET /admin/health` — proxies `/health` + `/backends/health` into one
    shape the page can poll (service status, websearch backend, admin_auth mode,
    impl count). Reuses the existing probes in `main.py` (extract the
    `websearch` probe helper to a shared spot or call the endpoint internally).
  - HTML: add a top "Status" strip — service ok, websearch_server
    ok/degraded/down, admin auth mode; poll `/admin/health` every ~15s.
  - HTML: flag orphan tools inline (red badge on the `impl` pill when orphaned).

**Acceptance**
- `/admin` shows a live status strip; killing `websearch_server` flips it to
  "down" within one poll.
- A tool with a bogus `impl` renders with an "orphan" badge; `orphans` is
  non-empty in `/admin/registry`.

---

## Phase 2 — Export + per-tool endpoint clarity (read-only)

**Goal:** Make the catalog portable and show how each tool is served.

**Changes**
- `app/admin.py`
  - `GET /admin/export?app=` — returns the registry slice as downloadable JSON
    (`Content-Disposition: attachment`). `app` omitted = full registry.
  - HTML: "Export" button (all apps + per active tab); a small "endpoint" column
    showing `/mcp/{app}/` and the resolved `execution` (server/client).

**Acceptance**
- Export downloads valid JSON that round-trips against the registry shape.
- Each tool row shows its MCP endpoint and execution mode.

---

## Phase 3 — "Try it" panel (read-tier invoke)

**Goal:** Exercise a tool from the browser without leaving `/admin`.

**Changes**
- `app/admin.py`
  - HTML: per-tool "Try" affordance on the expanded detail row — a form
    generated from `input_schema` (string/integer/boolean inputs), a "Run"
    button, and a result pane.
  - JS calls the **existing** `POST /tools/{name}/invoke?app=`; no new backend.
  - `write`-tier tools require an explicit confirm checkbox before Run is enabled.
- `app/main.py` — none (invoke endpoint already exists).

**Acceptance**
- Running `web_search` from the panel returns and displays results.
- `write`-tier tools cannot be run without ticking the confirm box.
- Invoke errors render the `{error}` payload, not a blank pane.

---

## Phase 4 — Enable/disable toggle (first write surface)

**Goal:** Flip `enabled` without hand-editing JSON. Highest-value write.

**Changes**
- `app/main.py`
  - Add `PATCH /tools/{name}/enabled?app=` and
    `PATCH /skills/{name}/enabled?app=` taking `{"enabled": bool}`,
    bearer-gated via the existing `_require_admin`. Implement with
    `registry.put_tool`/`put_skill` merge (partial update preserves other fields).
- `app/admin.py`
  - HTML: a toggle control per row. When `MCP_ADMIN_TOKEN` is set, the page
    needs the token — add a token field (Phase 5 formalises this; here, prompt
    for it on first write and keep in-memory only).
  - `/admin/registry` already exposes `enabled`; re-fetch after a successful
    toggle.

**Acceptance**
- Toggling a tool off removes it from `tools/list` over MCP and returns 409 on
  invoke; toggling on restores it.
- With a token set, an unauthenticated toggle returns 401.

---

## Phase 5 — Create/edit forms + auth UX (full authoring)

**Goal:** Author tools and skills from the UI over the existing CRUD endpoints.

**Changes**
- `app/admin.py`
  - HTML: "New / Edit" drawer. Tool form fields: `display_name`, `description`,
    `impl` (dropdown sourced from `/admin/registry.impls`), `tier`, `enabled`,
    `input_schema` (JSON textarea, validated client-side), `config` (JSON
    textarea). Skill form: `display_name`, `description`, `content`, `triggers`,
    `priority`, `enabled`.
  - Submits to the existing `PUT /tools/{name}` / `PUT /skills/{name}`.
  - Delete action wired to existing `DELETE` (confirm dialog).
  - **Auth UX:** a single admin-token field (in-memory, sent as
    `Authorization: Bearer` on writes); show a lock indicator reflecting
    `/health.admin_auth`.
- `app/main.py` — none new (CRUD exists); optionally validate `impl ∈ IMPLS` on
  `PUT` and reject unknown impls with 422.

**Acceptance**
- Creating a tool via the form makes it appear over MCP `tools/list` (when
  enabled) and invokable.
- Editing schema/config persists to `registry.json` and survives restart.
- Authoring a skill makes it appear over MCP `prompts/list` — first real skill.
- Bad JSON in schema/config is rejected client-side before submit.

---

## Phase 6 — Invocation metrics (needs a store)

**Goal:** Per-tool usage visibility. Deferred — introduces state the service
doesn't have today.

**Changes**
- `app/metrics.py` (new) — lightweight per-tool counters (count, last_used,
  error_count) persisted alongside the registry (`data/metrics.json`), updated
  in `toolimpl.invoke` call sites (`mcpserver.call_tool`, REST invoke).
- `app/admin.py` — `GET /admin/metrics` + a column/sparkline in the UI.

**Acceptance**
- Invoking a tool (MCP or REST) increments its count and updates `last_used`.
- Metrics survive restart and render per-tool in `/admin`.

**Open questions**
- Persistence cadence (write-through vs periodic flush) under concurrent invokes.
- Whether client-executed tools (tutor UI) should report usage back here at all.

---

## Sequencing & risk

| Phase | Surface | Risk | Depends on |
|-------|---------|------|------------|
| 1 Health + orphans | read | low | — |
| 2 Export + endpoints | read | low | — |
| 3 Try it | read (invoke) | low–med | — |
| 4 Enable toggle | **write** | med | — |
| 5 Authoring + auth | **write** | med–high | 4 (auth UX) |
| 6 Metrics | write (state) | med | new store |

Recommended order: **1 → 4 → 2 → 3 → 5 → 6** (health panel + enable toggle are
the highest signal per the architecture doc; defer metrics until the store
design is settled).
