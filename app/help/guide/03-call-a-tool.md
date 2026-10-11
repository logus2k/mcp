# Call a tool over REST

```
POST /tools/{name}/invoke?app={app}
Authorization: Bearer mcpk_…
X-On-Behalf-Of: <address>          (when acting for a person)
Content-Type: application/json

{"args": {...}}
```

The answer is `{"tool": name, "app": app, "result": ...}`. The result is whatever the tool returns: an object for
`web_search`, a text for `fetch_url` and `newsapi_search`.

```bash
curl -s -X POST "http://mcp-service:8080/tools/web_search/invoke?app=tutor" \
  -H "Authorization: Bearer $MCP_KEY" -H "X-On-Behalf-Of: ana.costa@bancoctt.pt" \
  -H "content-type: application/json" \
  -d '{"args": {"query": "kubernetes operator pattern", "max_results": 3}}'
```

## The arguments

They are validated against the tool's `input_schema` (JSON Schema 2020-12) before the tool runs. `GET /tools/{name}`
returns the record with the schema; the console's **Schema** tab shows it as a table. A mismatch answers `422`:

```json
{"error": {"code": "invalid_arguments", "message": "'query' is a required property", "path": "/"}}
```

## The app

`?app=` must name an app the tool is offered to (`404` otherwise). It may be omitted for a tool offered to one app only.

## Other answers

| Status | Meaning |
|---|---|
| `409` tool disabled | an administrator switched it off |
| `409` client-executed tool | the tool runs in the app's own page; the service only serves its schema |
| `502` | the implementation failed; the message is its own (`websearch 504: …`) |

## See also
- [Connect over MCP](04-connect-over-mcp.md)
- [Examples](07-examples.md)
