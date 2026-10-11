# Understand a call's record

| Column | Meaning |
|---|---|
| Time | when the call started |
| App | the app it was for (`?app=` or the endpoint's app) |
| Tool | the tool |
| Caller | the key's id; `console` for the admin token; your address when you ran it signed in; `anonymous` when nothing was presented |
| On behalf of | the person the caller acts for (`X-On-Behalf-Of`), or the signed-in person |
| Via | `rest` or `mcp` |
| Duration | how long the tool took |
| Status | ok, or the error the caller received |

## The errors you will see

- *invalid_arguments at /x* — the arguments did not match the schema; the property is named.
- *401: a write-tier tool needs an app key* — an anonymous caller tried a write tool.
- *401: an app key is required* — keys are required and none was presented.
- *403: this key belongs to app 'a', not 'b'* — a key used for another app's endpoint.
- *409: tool disabled* / *client-executed tool* — the tool is off, or the service does not run it.
- *502 …* — the implementation failed; the message is its own.

## Notes

- Arguments are recorded as a **digest** (a fingerprint), not as text, unless the record is set to keep them, and
  never for write tools.

## See also
- [Read the activity](05-01-read-the-activity.md)
- [The record and its retention](07-03-record-and-retention.md)
