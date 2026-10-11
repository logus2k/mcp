# Read a tool's schema

A tool's **input schema** says which arguments it takes: their names, types, which are required, their defaults.
Every call is checked against it before the tool runs. A tool may also declare an **output schema**: its result is
then returned as structured content too.

## Steps

1. Open the tool (select its row in **Tools**) and click the **Schema** tab.
2. The table lists each property with its type, whether it is required, its default and its description.
3. **Raw JSON** shows the schema as it is stored; the same button brings the table back.
4. Under the table: whether an output schema is declared, and the schema itself when there is one.

## Notes

- The **Overview** tab shows the tool's **annotations**, what an MCP client is told: *readOnlyHint* (a read tool),
  *destructiveHint* (a write tool marked destructive), *idempotentHint*.
- A call that does not match the schema is refused with the property that failed; it is recorded as an error.

## See also
- [Edit a tool](02-05-edit-a-tool.md)
- [Understand a call's record](05-03-understand-a-call.md)
