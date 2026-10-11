# Integration Guide

How an **application** or an **agent** uses MCP Server: it gets a **key** for its app, calls **tools** over REST or
over the MCP endpoint, and receives **skills** as prompts and resources. There is no library to install: the REST face
is plain HTTP and JSON, and the MCP face is the standard protocol every MCP client speaks.

## At a glance
- Internal address: `http://mcp-service:8080`. REST: `/tools/{name}/invoke?app={app}`. MCP: `/mcp/{app}/`.
- A program carries `Authorization: Bearer mcpk_…` (its app's key) and, when it acts for a person,
  `X-On-Behalf-Of: <address>`; an MCP client in a person's hands signs them in with OAuth 2.1 instead.
- Arguments are validated against the tool's schema; errors come back as `{"error": {"code", "message", "path"}}`.

## 1. Connect
- [Addresses, faces and apps](01-overview.md)
- [Keys and identity](02-keys-and-identity.md)
- [Sign in with OAuth 2.1](08-oauth.md)

## 2. Use
- [Call a tool over REST](03-call-a-tool.md)
- [Connect over MCP](04-connect-over-mcp.md)
- [Prompts and resources: the skills](05-prompts-and-resources.md)

## 3. Reference
- [Errors and limits](06-errors-and-limits.md)
- [Examples](07-examples.md)
