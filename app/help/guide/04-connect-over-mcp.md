# Connect over MCP

The MCP endpoint of an app is

```
http://mcp-service:8080/mcp/{app}/
```

Streamable HTTP, stateless, JSON responses; the key in the `Authorization` header of every request, the person in
`X-On-Behalf-Of`. Any MCP client connects to it.

## Claude Code

```bash
claude mcp add --transport http tutor http://mcp-service:8080/mcp/tutor/ \
  --header "Authorization: Bearer mcpk_…"
```

## Claude Desktop

```json
{"mcpServers": {"tutor": {"type": "http", "url": "http://mcp-service:8080/mcp/tutor/",
                          "headers": {"Authorization": "Bearer mcpk_…"}}}}
```

## What the client gets

- `initialize` — the server (`mcp-service`), the protocol, the capabilities `tools`, `prompts`, `resources`.
- `tools/list` — the app's enabled tools, each with its `inputSchema`, an `outputSchema` when declared, and
  **annotations**: `readOnlyHint` (a read tool), `destructiveHint` (a write tool marked destructive),
  `idempotentHint`.
- `tools/call` — the result as text, and as `structuredContent` when the tool declares an output schema. A refused or
  failed call is an `isError` result whose text carries the same code and message as the REST face.
- `prompts/list`, `prompts/get`, `resources/list`, `resources/read` — the skills: see the next page.

## A session with the official SDK (Python)

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

headers = {"Authorization": f"Bearer {KEY}", "X-On-Behalf-Of": user}
async with streamablehttp_client("http://mcp-service:8080/mcp/agent_runtime/", headers=headers) as (r, w, _):
    async with ClientSession(r, w) as s:
        await s.initialize()
        tools = (await s.list_tools()).tools
        res = await s.call_tool("fetch_url", {"url": "https://example.com", "max_chars": 2000})
```

## See also
- [Prompts and resources: the skills](05-prompts-and-resources.md)
- [Keys and identity](02-keys-and-identity.md)
