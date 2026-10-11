# Require keys from every caller

By default keys are **optional** for read-tier tools, so existing consumers keep working while they are given keys;
write-tier tools always need one. Once every consumer has a key, require them.

## Steps

1. Open **Apps**: every app that calls the service should show *key active*. The Overview lists the ones without.
2. Open **Activity** with *Only errors* off and look for *anonymous* callers in the last days; give them keys.
3. Set `MCP_REQUIRE_KEYS=1` in the service's environment and restart it.
4. The status bar reads *keys required*; an anonymous call is now refused with *an app key is required*.

## See also
- [Issue a key to an app](04-02-issue-a-key.md)
- [What needs attention](06-01-needs-attention.md)
