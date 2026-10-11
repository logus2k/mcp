# Addresses, faces and apps

## The address

Inside the domain's network, the service is at:

```
http://mcp-service:8080
```

On the domain, `https://logus2k.com/mcp-console/` reaches the same service, behind the administrators' sign-in: it is
for people and the console, not for programs.

## Two faces

| Face | Address | For |
|---|---|---|
| REST | `POST /tools/{name}/invoke?app={app}`, `GET /tools?app=`, `GET /tools/manifest?app=` | an application that calls a tool from its own code |
| MCP | `/mcp/{app}/` (Streamable HTTP, JSON-RPC) | an agent or an MCP client: `tools/list`, `tools/call`, `prompts/*`, `resources/*` |

Both go through the same pipeline: the caller is identified, the arguments are validated, the tool runs, the call is
recorded.

## Apps

A tool or a skill is **offered to apps**. Your program connects as one app: `?app=tutor` on REST, `/mcp/tutor/` on
MCP. It sees only what that app is offered, and its key is bound to that app.

```bash
curl -s "http://mcp-service:8080/tools/manifest?app=tutor" -H "Authorization: Bearer $MCP_KEY"
```

returns the enabled tools of app `tutor` as `{name, description, input_schema}`: what an orchestrator feeds a model.

## See also
- [Keys and identity](02-keys-and-identity.md)
