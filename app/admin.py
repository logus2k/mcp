"""Admin area — a browser view over the registry.

Reads are open (consistent with the rest of the REST read surface on the
internal network). Authoring actions in the page call the bearer-gated CRUD/PATCH
endpoints in main.py with an admin token the operator supplies in the UI; this
module itself only serves read-only data + the page.

    GET /admin            self-contained HTML page (no templates/static deps)
    GET /admin/registry   aggregate JSON across ALL apps (+ impl orphan analysis)
    GET /admin/health     service + backend liveness + admin-auth mode (polled)
    GET /admin/export     downloadable registry JSON (full or ?app= slice)

The probe helpers live here so main.py's /backends/health reuses them.
"""
from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app import registry, toolimpl

router = APIRouter()


# ── backend liveness (shared with main.backends_health) ─────────────────────
async def probe_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.get(url)
        return "degraded" if r.status_code >= 500 else "ok"
    except Exception:  # noqa: BLE001 — any connect/timeout means unreachable
        return "down"


async def backends_status() -> dict:
    return {"websearch_server": await probe_url(f"{toolimpl.WEBSEARCH_URL}/health")}


# ── analysis helpers ────────────────────────────────────────────────────────
def _execution(tool: dict) -> str:
    return (tool.get("config") or {}).get("execution", "server")


def _is_orphan(tool: dict) -> bool:
    """Server-executed tool bound to an impl that doesn't exist. Client-executed
    tools carry a client-side impl id this service never runs — never orphans."""
    return _execution(tool) != "client" and tool.get("impl") not in toolimpl.IMPLS


def _by_app(records: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in records:
        out.setdefault(r.get("app", "?"), []).append(r)
    return out


# ── data endpoints ──────────────────────────────────────────────────────────
@router.get("/admin/registry")
async def admin_registry():
    """Everything the admin page needs in one read — tools + skills across all
    apps, the impls the catalog can bind to, and impl-coverage analysis."""
    tools = registry.list_tools()
    skills = registry.list_skills()
    apps = sorted({r.get("app", "?") for r in tools + skills})
    impls = sorted(toolimpl.IMPLS.keys())
    referenced = {t.get("impl") for t in tools if _execution(t) != "client"}
    return JSONResponse({
        "apps": apps,
        "tools": tools,
        "skills": skills,
        "tools_by_app": _by_app(tools),
        "skills_by_app": _by_app(skills),
        "impls": impls,
        "orphans": [f"{t['app']}/{t['name']}" for t in tools if _is_orphan(t)],
        "unused_impls": [i for i in impls if i not in referenced],
        "counts": {
            "apps": len(apps),
            "tools": len(tools),
            "tools_enabled": sum(1 for t in tools if t.get("enabled", True)),
            "skills": len(skills),
            "skills_enabled": sum(1 for s in skills if s.get("enabled", True)),
        },
    })


@router.get("/admin/health")
async def admin_health():
    return JSONResponse({
        "service": "ok",
        "admin_auth": "bearer" if os.getenv("MCP_ADMIN_TOKEN", "") else "open",
        "impls": len(toolimpl.IMPLS),
        "backends": await backends_status(),
    })


@router.get("/admin/export")
async def admin_export(app: str | None = Query(None)):
    """Downloadable registry JSON — full registry, or a single-app slice."""
    tools = registry.list_tools(app)
    skills = registry.list_skills(app)
    payload = {"app": app or "all", "tools": tools, "skills": skills}
    fname = f"registry-{app or 'all'}.json"
    return JSONResponse(payload, headers={
        "Content-Disposition": f'attachment; filename="{fname}"'})


@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return HTMLResponse(_PAGE)


_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCP Server</title>
<style>
  :root, :root[data-theme="dark"] {
    --bg:#0f1115; --panel:#171a21; --line:#262b36; --fg:#e6e9ef; --muted:#8b93a7;
    --accent:#6ea8fe; --read:#2d6a4f; --read-fg:#d8f3e3; --write:#9a3412; --write-fg:#ffe6d5;
    --chip:#1f2530; --ok:#7ee2a8; --warn:#f0c674; --down:#ff9a9a;
    --detail:#10131a; --pre-bg:#0b0d12; --pre-fg:#cdd3e0;
    --primary:#1e3a5f; --danger:#3a1c1c; --danger-line:#7a3030;
    --slider:#3a3f4b; --knob:#cdd3e0; --overlay:rgba(0,0,0,.55);
    --orphan-bg:#5a1d1d; --orphan-fg:#ffd0d0;
  }
  :root[data-theme="light"] {
    --bg:#f7f8fa; --panel:#ffffff; --line:#dde1e8; --fg:#1c2128; --muted:#5b6473;
    --accent:#2563eb; --read:#1f7a4d; --read-fg:#eafff3; --write:#b8531f; --write-fg:#fff2e8;
    --chip:#eef1f5; --ok:#1f9d57; --warn:#b8860b; --down:#c0392b;
    --detail:#f1f3f7; --pre-bg:#f1f3f7; --pre-fg:#2a2f3a;
    --primary:#dbe7ff; --danger:#fbe3e3; --danger-line:#e3a0a0;
    --slider:#c2c8d2; --knob:#ffffff; --overlay:rgba(20,24,33,.4);
    --orphan-bg:#f6d3d3; --orphan-fg:#9a2222;
  }
  button.primary, button.danger { color:var(--fg); }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:14px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
  header { padding:16px 24px; border-bottom:1px solid var(--line);
           display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
  header h1 { font-size:16px; margin:0; font-weight:600; }
  header .sub { color:var(--muted); font-size:13px; }
  .status { display:flex; gap:14px; align-items:center; font-size:13px; color:var(--muted); }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px;
         background:var(--muted); vertical-align:middle; }
  .dot.ok{background:var(--ok)} .dot.degraded{background:var(--warn)} .dot.down{background:var(--down)}
  .counts { margin-left:auto; display:flex; gap:14px; color:var(--muted); font-size:13px; }
  .counts b { color:var(--fg); }
  .toolbar { padding:12px 24px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;
             border-bottom:1px solid var(--line); position:sticky; top:0; background:var(--bg); z-index:5; }
  input, select, textarea { background:var(--panel); border:1px solid var(--line);
             color:var(--fg); padding:7px 10px; border-radius:8px; outline:none; font:inherit; }
  input[type=search]{ width:260px; }
  .tabs { display:flex; gap:6px; flex-wrap:wrap; }
  .tab { background:var(--chip); border:1px solid var(--line); color:var(--muted);
         padding:6px 12px; border-radius:999px; cursor:pointer; font-size:13px; }
  .tab.active { color:var(--fg); border-color:var(--accent); }
  label.toggle { color:var(--muted); display:flex; gap:6px; align-items:center; cursor:pointer; }
  .spacer { margin-left:auto; }
  button { background:var(--chip); border:1px solid var(--line); color:var(--fg);
           padding:7px 12px; border-radius:8px; cursor:pointer; font:inherit; }
  button:hover { border-color:var(--accent); }
  button.primary { background:var(--primary); border-color:var(--accent); }
  button.danger { background:var(--danger); border-color:var(--danger-line); }
  button.ghost { background:transparent; }
  main { padding:20px 24px 80px; }
  section h2 { font-size:13px; text-transform:uppercase; letter-spacing:.06em;
               color:var(--muted); margin:24px 0 10px; }
  table { width:100%; border-collapse:collapse; }
  th { text-align:left; font-size:12px; color:var(--muted); font-weight:500;
       padding:8px 10px; border-bottom:1px solid var(--line); }
  td { padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top; }
  tr.row { cursor:pointer; } tr.row:hover { background:var(--panel); }
  .name { font-weight:600; }
  .desc { color:var(--muted); max-width:480px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:6px; font-size:12px; }
  .read { background:var(--read); color:var(--read-fg); }
  .write { background:var(--write); color:var(--write-fg); }
  .orphan { background:var(--orphan-bg); color:var(--orphan-fg); margin-left:6px; }
  .on { color:var(--ok); } .offt { color:var(--muted); }
  .pill { background:var(--chip); border:1px solid var(--line); color:var(--muted);
          padding:1px 7px; border-radius:6px; font-size:12px; font-family:ui-monospace,monospace; }
  tr.detail td { background:var(--detail); }
  .grid2 { display:grid; gap:10px; grid-template-columns:1fr 1fr; }
  pre { margin:0; padding:12px; background:var(--pre-bg); border:1px solid var(--line);
        border-radius:8px; overflow:auto; color:var(--pre-fg); font:12px/1.5 ui-monospace,monospace; max-height:280px; }
  .empty { color:var(--muted); padding:18px 10px; }
  .err { color:var(--down); }
  a { color:var(--accent); }
  /* switch */
  .switch { position:relative; display:inline-block; width:36px; height:20px; }
  .switch input { display:none; }
  .slider { position:absolute; inset:0; background:var(--slider); border-radius:999px; transition:.15s; }
  .slider:before { content:""; position:absolute; width:14px; height:14px; left:3px; top:3px;
                   background:var(--knob); border-radius:50%; transition:.15s; }
  .switch input:checked + .slider { background:var(--read); }
  .switch input:checked + .slider:before { transform:translateX(16px); }
  /* try panel + forms */
  .panel { background:var(--pre-bg); border:1px solid var(--line); border-radius:8px; padding:12px; }
  .field { display:flex; flex-direction:column; gap:4px; margin-bottom:10px; }
  .field label { color:var(--muted); font-size:12px; }
  .field .req { color:var(--warn); }
  .actions { display:flex; gap:8px; align-items:center; margin-top:8px; flex-wrap:wrap; }
  .rowflex { display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap; }
  .rowflex > div { flex:1; min-width:260px; }
  /* modal */
  .overlay { position:fixed; inset:0; background:var(--overlay); display:none;
             align-items:flex-start; justify-content:center; z-index:50; overflow:auto; padding:40px 16px; }
  .overlay.show { display:flex; }
  .modal { background:var(--panel); border:1px solid var(--line); border-radius:12px;
           width:640px; max-width:100%; padding:20px; }
  .modal h3 { margin:0 0 14px; font-size:15px; }
  .modal textarea { width:100%; font:12px/1.5 ui-monospace,monospace; resize:vertical; }
  .modal input, .modal select { width:100%; }
</style>
</head>
<body>
<header>
  <h1>MCP Server</h1>
  <div class="status" id="status"></div>
  <div class="counts" id="counts"></div>
</header>
<div class="toolbar">
  <input id="q" type="search" placeholder="filter by name, description, impl…">
  <div class="tabs" id="apptabs"></div>
  <label class="toggle"><input type="checkbox" id="enabledOnly"> enabled only</label>
  <div class="spacer"></div>
  <button data-action="theme" id="themeBtn" title="Toggle light / dark">🌙 Dark</button>
  <!-- label shows the theme you'll switch TO; default theme is light -->

  <button data-action="new" data-kind="tool">+ Tool</button>
  <button data-action="new" data-kind="skill">+ Skill</button>
  <button data-action="export">Export</button>
  <input id="token" type="password" placeholder="admin token (for writes)" style="width:180px">
</div>
<main id="main"><div class="empty">loading…</div></main>

<div class="overlay" id="overlay"><div class="modal" id="modal"></div></div>

<script>
let DATA = null, app = "__all__", q = "", enabledOnly = false;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const token = () => $("token").value.trim();
const tierBadge = t => `<span class="badge ${t==="write"?"write":"read"}">${esc(t||"read")}</span>`;
const execOf = r => (r.config && r.config.execution) || "server";
const isOrphan = r => DATA && DATA.orphans.includes(`${r.app}/${r.name}`);
const getTool = (a,n) => DATA.tools.find(t => t.app===a && t.name===n);
const getSkill = (a,n) => DATA.skills.find(s => s.app===a && s.name===n);

function authHeaders(json) {
  const h = json ? {"content-type":"application/json"} : {};
  if (token()) h["Authorization"] = "Bearer " + token();
  return h;
}
async function writeReq(method, url, body) {
  const r = await fetch(url, {method, headers: authHeaders(!!body),
    body: body ? JSON.stringify(body) : undefined});
  if (r.status === 401) { alert("401 — admin token required or wrong."); throw new Error("401"); }
  if (!r.ok) { let t; try { t = JSON.stringify(await r.json()); } catch { t = r.statusText; }
    alert(`${method} failed (${r.status}): ${t}`); throw new Error(String(r.status)); }
  return r.json();
}

function matches(r) {
  if (enabledOnly && r.enabled === false) return false;
  if (app !== "__all__" && r.app !== app) return false;
  if (!q) return true;
  return [r.name, r.display_name, r.description, r.impl, r.app].join(" ").toLowerCase().includes(q);
}

// ── rendering ──────────────────────────────────────────────────────────────
function switchHtml(kind, r) {
  const on = r.enabled !== false;
  return `<label class="switch" data-action="toggle" data-kind="${kind}" data-app="${esc(r.app)}" data-name="${esc(r.name)}">
    <input type="checkbox" ${on?"checked":""}><span class="slider"></span></label>`;
}

function tryFormHtml(r) {
  const props = (r.input_schema && r.input_schema.properties) || {};
  const req = new Set((r.input_schema && r.input_schema.required) || []);
  let fields = Object.keys(props).map(k => {
    const p = props[k] || {}, t = p.type || "string";
    const lbl = `<label>${esc(k)} ${req.has(k)?'<span class="req">*</span>':''} <span class="pill">${esc(t)}</span></label>`;
    let inp;
    if (t === "boolean") inp = `<input type="checkbox" data-arg="${esc(k)}" data-type="boolean">`;
    else if (t === "integer" || t === "number") inp = `<input type="number" data-arg="${esc(k)}" data-type="${t}" placeholder="${esc(p.description||'')}">`;
    else inp = `<input type="text" data-arg="${esc(k)}" data-type="string" placeholder="${esc(p.description||'')}">`;
    return `<div class="field">${lbl}${inp}</div>`;
  }).join("");
  if (!fields) fields = `<div class="sub" style="color:var(--muted)">no input parameters</div>`;
  const wr = r.tier === "write"
    ? `<label class="toggle"><input type="checkbox" data-confirm> confirm: this is a write tool</label>` : "";
  const clientNote = execOf(r) === "client"
    ? `<div class="sub" style="color:var(--warn);margin-bottom:8px">client-executed tool — invoking here runs the server path only; the real action lives in the consuming app.</div>` : "";
  return `<div class="panel"><div style="color:var(--muted);font-size:12px;margin-bottom:8px">Try it</div>
    ${clientNote}${fields}
    <div class="actions">${wr}
      <button class="primary" data-action="run" data-app="${esc(r.app)}" data-name="${esc(r.name)}" ${r.tier==="write"?'disabled data-needsconfirm':''}>Run</button>
    </div>
    <pre class="result" style="display:none;margin-top:10px"></pre></div>`;
}

function toolTable(rows) {
  if (!rows.length) return `<div class="empty">No tools match.</div>`;
  let html = `<table><thead><tr>
    <th>Name</th><th>App</th><th>Tier</th><th>Impl</th><th>Exec</th><th>Endpoint</th><th>Enabled</th><th>Description</th>
    </tr></thead><tbody>`;
  for (const r of rows) {
    const schema = JSON.stringify(r.input_schema || {}, null, 2);
    const cfg = JSON.stringify(r.config || {}, null, 2);
    const orphan = isOrphan(r) ? `<span class="badge orphan" title="impl not in IMPLS">orphan</span>` : "";
    html += `<tr class="row" data-action="expand">
      <td class="name">${esc(r.name)}</td>
      <td><span class="pill">${esc(r.app)}</span></td>
      <td>${tierBadge(r.tier)}</td>
      <td><span class="pill">${esc(r.impl)}</span>${orphan}</td>
      <td><span class="pill">${esc(execOf(r))}</span></td>
      <td><span class="pill">/mcp/${esc(r.app)}/</span></td>
      <td>${switchHtml("tool", r)}</td>
      <td class="desc">${esc(r.description)}</td>
    </tr>
    <tr class="detail" style="display:none"><td colspan="8">
      <div class="rowflex">
        <div>
          <div class="grid2">
            <div><div class="sub" style="color:var(--muted);margin-bottom:6px">input_schema</div><pre>${esc(schema)}</pre></div>
            <div><div class="sub" style="color:var(--muted);margin-bottom:6px">config</div><pre>${esc(cfg)}</pre></div>
          </div>
          <div class="actions">
            <button data-action="edit" data-kind="tool" data-app="${esc(r.app)}" data-name="${esc(r.name)}">Edit</button>
            <button class="danger" data-action="delete" data-kind="tool" data-app="${esc(r.app)}" data-name="${esc(r.name)}">Delete</button>
          </div>
        </div>
        <div>${tryFormHtml(r)}</div>
      </div>
    </td></tr>`;
  }
  return html + `</tbody></table>`;
}

function skillTable(rows) {
  if (!rows.length) return `<div class="empty">No skills registered.</div>`;
  let html = `<table><thead><tr>
    <th>Name</th><th>App</th><th>Priority</th><th>Enabled</th><th>Triggers</th><th>Description</th>
    </tr></thead><tbody>`;
  for (const r of rows) {
    html += `<tr class="row" data-action="expand">
      <td class="name">${esc(r.name)}</td>
      <td><span class="pill">${esc(r.app)}</span></td>
      <td>${esc(r.priority ?? "")}</td>
      <td>${switchHtml("skill", r)}</td>
      <td>${(r.triggers||[]).map(t=>`<span class="pill">${esc(t)}</span>`).join(" ")}</td>
      <td class="desc">${esc(r.description)}</td>
    </tr>
    <tr class="detail" style="display:none"><td colspan="6">
      <pre>${esc(r.content || "")||"(no content)"}</pre>
      <div class="actions">
        <button data-action="edit" data-kind="skill" data-app="${esc(r.app)}" data-name="${esc(r.name)}">Edit</button>
        <button class="danger" data-action="delete" data-kind="skill" data-app="${esc(r.app)}" data-name="${esc(r.name)}">Delete</button>
      </div></td></tr>`;
  }
  return html + `</tbody></table>`;
}

function render() {
  const tools = DATA.tools.filter(matches);
  const skills = DATA.skills.filter(matches);
  $("main").innerHTML =
    `<section><h2>Tools · ${tools.length}</h2>${toolTable(tools)}</section>
     <section><h2>Skills · ${skills.length}</h2>${skillTable(skills)}</section>`;
}

function renderTabs() {
  const tabs = ["__all__", ...DATA.apps];
  $("apptabs").innerHTML = tabs.map(a =>
    `<span class="tab ${a===app?"active":""}" data-action="tab" data-a="${esc(a)}">${a==="__all__"?"all apps":esc(a)}</span>`).join("");
}

function renderCounts() {
  const c = DATA.counts;
  $("counts").innerHTML =
    `<span><b>${c.apps}</b> apps</span>
     <span><b>${c.tools_enabled}</b>/<b>${c.tools}</b> tools</span>
     <span><b>${c.skills_enabled}</b>/<b>${c.skills}</b> skills</span>`
    + (DATA.orphans.length ? ` <span class="err"><b>${DATA.orphans.length}</b> orphan</span>` : "");
}

// ── modal (create / edit) ────────────────────────────────────────────────────
function openModal(kind, rec) {
  const editing = !!rec;
  let body;
  if (kind === "tool") {
    const opts = DATA.impls.map(i => `<option ${rec&&rec.impl===i?"selected":""}>${esc(i)}</option>`).join("");
    body = `
      <div class="field"><label>app</label><input data-f="app" value="${esc(rec?rec.app:app==='__all__'?'':app)}" ${editing?"readonly":""}></div>
      <div class="field"><label>name <span class="req">*</span></label><input data-f="name" value="${esc(rec?rec.name:'')}" ${editing?"readonly":""}></div>
      <div class="field"><label>display_name</label><input data-f="display_name" value="${esc(rec?rec.display_name:'')}"></div>
      <div class="field"><label>description</label><input data-f="description" value="${esc(rec?rec.description:'')}"></div>
      <div class="grid2">
        <div class="field"><label>impl</label><select data-f="impl">${opts}</select></div>
        <div class="field"><label>tier</label><select data-f="tier">
          <option ${rec&&rec.tier==='read'?'selected':''}>read</option>
          <option ${rec&&rec.tier==='write'?'selected':''}>write</option></select></div>
      </div>
      <div class="field"><label>input_schema (JSON)</label><textarea data-f="input_schema" rows="6">${esc(JSON.stringify(rec?(rec.input_schema||{}):{type:"object",properties:{}}, null, 2))}</textarea></div>
      <div class="field"><label>config (JSON)</label><textarea data-f="config" rows="4">${esc(JSON.stringify(rec?(rec.config||{}):{}, null, 2))}</textarea></div>
      <label class="toggle"><input type="checkbox" data-f="enabled" ${!rec||rec.enabled!==false?"checked":""}> enabled</label>`;
  } else {
    body = `
      <div class="field"><label>app</label><input data-f="app" value="${esc(rec?rec.app:app==='__all__'?'':app)}" ${editing?"readonly":""}></div>
      <div class="field"><label>name <span class="req">*</span></label><input data-f="name" value="${esc(rec?rec.name:'')}" ${editing?"readonly":""}></div>
      <div class="field"><label>display_name</label><input data-f="display_name" value="${esc(rec?rec.display_name:'')}"></div>
      <div class="field"><label>description</label><input data-f="description" value="${esc(rec?rec.description:'')}"></div>
      <div class="field"><label>content</label><textarea data-f="content" rows="8">${esc(rec?rec.content:'')}</textarea></div>
      <div class="grid2">
        <div class="field"><label>triggers (comma-separated)</label><input data-f="triggers" value="${esc(rec?(rec.triggers||[]).join(', '):'')}"></div>
        <div class="field"><label>priority</label><input type="number" data-f="priority" value="${esc(rec?(rec.priority??100):100)}"></div>
      </div>
      <label class="toggle"><input type="checkbox" data-f="enabled" ${!rec||rec.enabled!==false?"checked":""}> enabled</label>`;
  }
  $("modal").dataset.kind = kind;
  $("modal").innerHTML = `<h3>${editing?"Edit":"New"} ${kind}</h3>${body}
    <div class="actions" style="margin-top:16px">
      <button class="primary" data-action="save">Save</button>
      <button data-action="close">Cancel</button>
      <span class="err" id="modalErr"></span>
    </div>`;
  $("overlay").classList.add("show");
}
function closeModal() { $("overlay").classList.remove("show"); }

function readField(f) {
  const el = $("modal").querySelector(`[data-f="${f}"]`);
  if (!el) return undefined;
  if (el.type === "checkbox") return el.checked;
  return el.value;
}
async function saveModal() {
  const kind = $("modal").dataset.kind;
  const name = (readField("name")||"").trim();
  const app_ = (readField("app")||"").trim();
  if (!name || !app_) { $("modalErr").textContent = "app and name are required"; return; }
  let payload;
  try {
    if (kind === "tool") {
      payload = {
        display_name: readField("display_name"), description: readField("description"),
        impl: readField("impl"), tier: readField("tier"), enabled: readField("enabled"),
        input_schema: JSON.parse(readField("input_schema") || "{}"),
        config: JSON.parse(readField("config") || "{}"),
      };
    } else {
      payload = {
        display_name: readField("display_name"), description: readField("description"),
        content: readField("content"), enabled: readField("enabled"),
        priority: parseInt(readField("priority") || "100", 10),
        triggers: (readField("triggers")||"").split(",").map(s=>s.trim()).filter(Boolean),
      };
    }
  } catch (e) { $("modalErr").textContent = "invalid JSON: " + e.message; return; }
  const base = kind === "tool" ? "tools" : "skills";
  await writeReq("PUT", `${base}/${encodeURIComponent(name)}?app=${encodeURIComponent(app_)}`, payload);
  closeModal(); await load();
}

// ── actions ──────────────────────────────────────────────────────────────────
async function runTool(btn) {
  const detail = btn.closest(".panel");
  const args = {};
  detail.querySelectorAll("[data-arg]").forEach(el => {
    const k = el.dataset.arg, t = el.dataset.type;
    if (t === "boolean") { if (el.checked) args[k] = true; }
    else if (el.value !== "") args[k] = (t==="integer"||t==="number") ? Number(el.value) : el.value;
  });
  const out = detail.querySelector(".result");
  out.style.display = "block"; out.textContent = "running…";
  const r = await fetch(`tools/${encodeURIComponent(btn.dataset.name)}/invoke?app=${encodeURIComponent(btn.dataset.app)}`,
    {method:"POST", headers:{"content-type":"application/json"}, body: JSON.stringify({args})});
  let j; try { j = await r.json(); } catch { j = {error:"non-JSON response"}; }
  out.textContent = JSON.stringify(j, null, 2);
  out.classList.toggle("err", !r.ok);
}

async function toggle(el) {
  const inp = el.querySelector("input");
  const base = el.dataset.kind === "tool" ? "tools" : "skills";
  try {
    await writeReq("PATCH", `${base}/${encodeURIComponent(el.dataset.name)}/enabled?app=${encodeURIComponent(el.dataset.app)}`,
      {enabled: inp.checked});
    const rec = el.dataset.kind === "tool" ? getTool(el.dataset.app, el.dataset.name) : getSkill(el.dataset.app, el.dataset.name);
    if (rec) rec.enabled = inp.checked;
    renderCounts();
  } catch { inp.checked = !inp.checked; }  // revert on failure
}

async function del(kind, app_, name) {
  if (!confirm(`Delete ${kind} ${app_}/${name}?`)) return;
  const base = kind === "tool" ? "tools" : "skills";
  await writeReq("DELETE", `${base}/${encodeURIComponent(name)}?app=${encodeURIComponent(app_)}`);
  await load();
}

// ── event delegation ─────────────────────────────────────────────────────────
document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const a = el.dataset.action;
  if (a === "toggle") { e.stopPropagation(); return; }       // handled on change
  if (a === "run") {
    if (el.dataset.needsconfirm) return;
    return runTool(el);
  }
  if (a === "expand") {
    const d = el.nextElementSibling;
    if (d && d.classList.contains("detail")) d.style.display = d.style.display === "none" ? "" : "none";
    return;
  }
  if (a === "tab") { app = el.dataset.a; renderTabs(); render(); return; }
  if (a === "new") return openModal(el.dataset.kind, null);
  if (a === "edit") {
    e.stopPropagation();
    const rec = el.dataset.kind === "tool" ? getTool(el.dataset.app, el.dataset.name) : getSkill(el.dataset.app, el.dataset.name);
    return openModal(el.dataset.kind, rec);
  }
  if (a === "delete") { e.stopPropagation(); return del(el.dataset.kind, el.dataset.app, el.dataset.name); }
  if (a === "save") return saveModal();
  if (a === "close") return closeModal();
  if (a === "export") {
    const slice = app === "__all__" ? "" : `?app=${encodeURIComponent(app)}`;
    window.location = "admin/export" + slice; return;
  }
  if (a === "theme") return setTheme(
    document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light");
});

// ── theme ────────────────────────────────────────────────────────────────────
function setTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  try { localStorage.setItem("mcp-admin-theme", t); } catch {}
  // Button shows the theme you'll switch TO (the opposite of the current one).
  $("themeBtn").textContent = t === "light" ? "🌙 Dark" : "☀️ Light";
}
function initTheme() {
  let t;
  try { t = localStorage.getItem("mcp-admin-theme"); } catch {}
  if (!t) t = "light";  // default theme at startup
  setTheme(t);
}

// toggle (change) + write-tool confirm gating
document.addEventListener("change", (e) => {
  const sw = e.target.closest("[data-action=toggle]");
  if (sw) return toggle(sw);
  if (e.target.matches("[data-confirm]")) {
    const btn = e.target.closest(".panel").querySelector("[data-action=run]");
    if (e.target.checked) { btn.disabled = false; delete btn.dataset.needsconfirm; }
    else { btn.disabled = true; btn.dataset.needsconfirm = "1"; }
  }
});

$("overlay").addEventListener("click", e => { if (e.target === $("overlay")) closeModal(); });
$("q").addEventListener("input", e => { q = e.target.value.trim().toLowerCase(); render(); });
$("enabledOnly").addEventListener("change", e => { enabledOnly = e.target.checked; render(); });

// ── boot ─────────────────────────────────────────────────────────────────────
async function loadHealth() {
  try {
    const h = await (await fetch("admin/health")).json();
    const b = h.backends || {};
    const dots = Object.entries(b).map(([k,v]) => `<span><span class="dot ${v}"></span>${esc(k)}</span>`).join("");
    $("status").innerHTML =
      `<span><span class="dot ${h.service==='ok'?'ok':'down'}"></span>service</span>
       ${dots}
       <span>🔒 ${esc(h.admin_auth)}</span>`;
  } catch { $("status").innerHTML = `<span><span class="dot down"></span>status unavailable</span>`; }
}
async function load() {
  try { DATA = await (await fetch("admin/registry")).json(); }
  catch (e) { $("main").innerHTML = `<div class="empty err">Failed to load registry: ${esc(e)}</div>`; return; }
  renderCounts(); renderTabs(); render();
}
initTheme(); loadHealth(); setInterval(loadHealth, 15000); load();
</script>
</body>
</html>
"""
