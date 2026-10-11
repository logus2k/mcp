# Examples

## Python: call a tool for a signed-in person

```python
import httpx, os
BASE, KEY = "http://mcp-service:8080", os.environ["MCP_KEY"]

def web_search(query: str, user: str, n: int = 5) -> dict:
    r = httpx.post(f"{BASE}/tools/web_search/invoke", params={"app": "tutor"},
                   headers={"Authorization": f"Bearer {KEY}", "X-On-Behalf-Of": user},
                   json={"args": {"query": query, "max_results": n}}, timeout=90)
    if r.status_code == 422:
        raise ValueError(r.json()["error"]["message"])
    r.raise_for_status()
    return r.json()["result"]
```

## Python: offer an app's tools to a model

```python
specs = httpx.get(f"{BASE}/tools/manifest", params={"app": "agent_runtime"},
                  headers={"Authorization": f"Bearer {KEY}"}).json()["tools"]
# each spec: {"name", "description", "input_schema"} — the shape a chat completion's tools take
```

## Python: a skill as a system prompt

```python
skill = httpx.post(f"{BASE}/skills/cite_with_tag/render", json={"arguments": {"kb_tool": "kb_search"}}).json()
system = skill["messages"][0]["content"]
```

## curl: list, call, render

```bash
curl -s "$BASE/tools?app=tutor" -H "Authorization: Bearer $MCP_KEY" | jq '.tools[].name'
curl -s -X POST "$BASE/tools/fetch_url/invoke?app=agent_runtime" -H "Authorization: Bearer $MCP_KEY" \
  -H "content-type: application/json" -d '{"args": {"url": "https://example.com", "max_chars": 500}}'
curl -s -X POST "$BASE/skills/pt_pt_style/render" -H "content-type: application/json" -d '{"arguments": {}}'
```

## An agent session (the official MCP SDK)

See [Connect over MCP](04-connect-over-mcp.md): `initialize`, `list_tools`, `call_tool`, `list_prompts`, `get_prompt`,
`list_resources`, `read_resource`, with the key in the headers.

## See also
- [Call a tool over REST](03-call-a-tool.md)
