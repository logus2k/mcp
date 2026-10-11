# Find a tool

**Tools** lists every tool the service offers, with the apps it is offered to, its tier, where it runs, its
implementation, when it was last used and how many calls it had in the last 24 hours.

## Steps

1. Click **Tools** in the side menu (or press `/`).
2. Type in the filter: it matches the name, the description, the implementation and the apps.
3. Click an app chip to see only what that app is offered; **read** or **write** to see one tier; **enabled only**
   to hide what is disabled.
4. Select a row: the drawer opens on the tool's **Overview**.

## What the columns mean

- **Apps** — the apps the tool is offered to. The same tool is defined once and offered to several.
- **Tier** — *read* tools only look things up; *write* tools change something outside the service and always need
  a key or an administrator.
- **Exec** — *server*: the service runs it; *client*: the app's own page runs it, and the service only serves its
  schema.
- **Last used** — from the record; *never* means no call in the retained window; *client* means the service never
  runs it.
- **Enabled** — the switch; a disabled tool disappears from every app's list.

## See also
- [Read a tool's schema](02-02-read-a-tools-schema.md)
- [Try a tool](02-03-try-a-tool.md)
