# The record and its retention

Every call is recorded with its app, tool, caller, person, transport, outcome and duration. Arguments are recorded
as a **digest** (a fingerprint that tells identical calls apart) by default.

- `MCP_RECORD_ARGS=1` keeps the arguments of **read-tier** tools as text; write-tier arguments are never kept.
- `MCP_RETENTION_DAYS` (90) is how long rows are kept; older ones are pruned daily.

Settings shows the current values; the status bar's *record* item sums them up.

## See also
- [Understand a call's record](05-03-understand-a-call.md)
- [Filter and export the activity](05-02-filter-and-export.md)
