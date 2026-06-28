# mcp-service

Shared **tool + skill host** with two faces:

1. **Standard MCP** at `/mcp/` (Streamable-HTTP, official `mcp` SDK). Any MCP
   client connects and gets `tools/list` · `tools/call` · `prompts/list` ·
   `prompts/get`. Tools → MCP tools; skills → MCP prompts. This is the reusable,
   interoperable surface other tools/agents connect to.
2. **Management REST** — CRUD for tools + skills (the job2cool admin UI), plus
   `POST /tools/{name}/invoke` and `GET /tools/manifest`. (MCP is a consumption
   protocol, not authoring — so authoring lives here.)

## Model
- **Tools** are declarative catalog entries (name, JSON-schema, which built-in
  `impl`, config, enabled). Implementations ship with the service
  (`app/toolimpl.py`); the UI never authors executable code (secure by design).
- **Skills** are reusable instruction templates (content + triggers). Exposed as
  MCP prompts. Trigger-based auto-injection is a consumer concern.

## Networks
- `noted-network` — apps (job2cool-backend) reach mcp-service.
- `mcp_internal` — mcp-service reaches the isolated `websearch_server`.
  `web_search` delegates to `websearch_server /search`.

## Admin area (read-only)
Browser view over the whole registry (all apps at once) at **`/admin`** — search,
filter by app, toggle enabled-only, expand each tool's `input_schema`/`config`.
Backed by `GET /admin/registry` (aggregate JSON). Consult-only; authoring stays on
the CRUD REST face below.

## REST quick-ref (default `?app=job2cool`)
```
GET    /health
GET    /admin                 GET /admin/registry      (read-only browser view)
GET    /tools                 GET /tools/manifest
PUT    /tools/{name}          DELETE /tools/{name}
POST   /tools/{name}/invoke   {"args": {...}}
GET    /skills                PUT /skills/{name}    DELETE /skills/{name}
```

## Run
```sh
docker network create mcp_internal   # shared with websearch_server (once)
docker compose up -d --build
curl -s localhost:4950/health
curl -s -XPOST localhost:4950/tools/web_search/invoke \
     -H 'content-type: application/json' -d '{"args":{"query":"kubernetes operator pattern","max_results":3}}'
```
