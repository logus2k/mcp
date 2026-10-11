# Settings

**Settings** (the side menu's bottom item, then *Settings*; or **View** › **Settings**) shows how the service is
configured and what binds to what.

- **Implementations** — the functions shipped with this version, each with the tools bound to it and their apps.
  *Orphans* are tools bound to an implementation that does not exist; *unused* implementations have no tool.
- **Backends** — each with its state.
- **Auth and retention** — the sign-in (Microsoft Entra ID through the domain proxy, or off), whether the admin token
  is set, the keys mode, whether the record keeps arguments, and the retention.
- **Export and import** — the registry as JSON (all, or one app), the activity as CSV, and an import with a dry run.

The values under *Auth and retention* are set in the service's environment, not here; the page tells you which
variable sets each.

## See also
- [Export and import the registry](06-04-export-and-import.md)
- [Who may write](07-01-who-may-write.md)
