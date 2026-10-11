# Errors and limits

## The error shape

REST answers `{"error": {"code": "...", "message": "...", "path": "..."}}` with the status; MCP answers an `isError`
result whose text is `code: message (at path)`.

| Code | Status | Meaning |
|---|---|---|
| `unauthorized` | 401 | no key where one is needed, or an unknown, revoked or expired key |
| `forbidden` | 403 | a key for another app |
| `invalid_arguments` | 422 | the arguments do not match the schema; `path` points at the property |
| `disabled` | 409 | the tool is switched off |
| `client_executed` | 409 | the tool runs in the app's page, not here |
| `tool_failed` | 502 | the implementation failed; the message is its own |

An unknown tool, or a tool not offered to the app: `404` on REST, *unknown or disabled tool* on MCP.

## Limits

- Tools answer within their own timeouts: `web_search` up to 90 s, `fetch_url` 30 s, `newsapi_search` 30 s.
- `fetch_url` returns at most `max_chars` characters (10 000 by default); `web_search` at most 25 results.
- A key expires on its date (at most 365 days); an app may hold 20 active keys.

## What is recorded

Every call: when, the app, the tool, the caller (your key's id), the person (`X-On-Behalf-Of`), the transport, the
outcome, the duration, and a digest of the arguments. The arguments themselves are kept only for read-tier tools when
the service is set to keep them, and never for write-tier tools. Rows are kept 90 days.

## Good practice

- Send `X-On-Behalf-Of` whenever a person is behind the call.
- Read `tools/manifest` (or `tools/list`) at start-up rather than hard-coding schemas: a tool's schema may change.
- Treat a `422` as your bug, a `502` as the backend's, a `401`/`403` as a key to fix.

## See also
- [Keys and identity](02-keys-and-identity.md)
