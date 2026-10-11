# Keys and identity

## The key

An administrator registers your app in the console's catalog (**Apps › New app**: owner, contact, status) and
issues it a key (**Apps › New key**). It is `mcpk_` + 43 characters, shown
once, bound to one app, with an expiry. Send it on every call:

```
Authorization: Bearer mcpk_…
```

Treat it as a password: a secret store or an environment variable, never source code, a URL or a log. One key per
program, named after it, so it can be revoked alone.

## What a key may do

- **read-tier** tools: with or without a key while keys are *optional* (the service's default during roll-out); with a
  key once keys are *required*.
- **write-tier** tools (they change something outside the service): always with a key.
- A key used for another app's endpoint is refused with `403`.

## The person

When your application acts for a person, name them:

```
X-On-Behalf-Of: ana.costa@bancoctt.pt
```

The address is recorded with the call (the console's Activity shows it) and is how an audit answers "what left the
network for this person". It is recorded as declared by your application; take it from your own sign-in, never from a
request field.

## Errors

| Status | Meaning |
|---|---|
| `401` unknown, revoked or expired key | the key presented is not accepted |
| `401` a write-tier tool needs an app key | you called a write tool without a key |
| `401` an app key is required | keys are required and you sent none |
| `403` this key belongs to app 'a', not 'b' | the key is for another app |

## See also
- [Call a tool over REST](03-call-a-tool.md)
- [Errors and limits](06-errors-and-limits.md)
