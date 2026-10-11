# Create a tool

A tool is a **catalog entry**: a name, a description, which shipped **implementation** runs it, its schema, its tier,
and the apps it is offered to. The console never authors code: the implementations ship with the service, and a
tool binds to one of them.

## Steps

1. Click **+ New tool** (Tools view) or **Catalog** › **New tool…**.
2. Give it a **name** (letters, digits, underscores; it cannot change later) and a display name.
3. Write the **description** the model will read: what the tool does and when to use it.
4. List the **apps** it is offered to, comma-separated. The Tools filter's app is proposed.
5. Choose the **tier** (*read* or *write*), the **execution** (*server*, or *client* for a tool the app's page runs),
   and the **implementation** from the list; for a client tool, name the client's own implementation id.
6. For a write tool, tick **destructive** if it removes or overwrites something; tick **idempotent** if calling it
   twice is the same as once.
7. Write the **input schema** (JSON Schema): its properties, types, descriptions, defaults and `required` list. An
   **output schema** is optional. **Config** holds per-tool settings the implementation reads.
8. Click **Save…**: the record to be created is shown; click **Save tool**.

## Notes

- A schema that is not valid JSON Schema is refused with the reason.
- The new tool is version 1; every later save adds a version to its **History**.

## See also
- [Edit a tool](02-05-edit-a-tool.md)
- [Offer a tool to another app](02-07-offer-a-tool-to-another-app.md)
