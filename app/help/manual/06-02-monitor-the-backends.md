# Monitor the backends

The tools depend on **backends**: the isolated web-search browser, Jenkins (for the SDLC sensors), the NewsAPI key,
the proxy's configuration mount. The console probes them.

## Where to look

- **Monitoring** in the top menu — the service and each backend with a dot and its state; the keys mode; how many
  items need attention; **Refresh health**.
- **The status bar** — at the right, *backends n ok*, or how many are down or degraded. Click it for Settings.
- **Settings** › **Backends** — the same, with the implementations that depend on each.

## Notes

- The health is refreshed every 30 seconds, and on **Refresh health**.
- A backend that is down does not take the service down: calls to the tools that need it fail with its error, and
  the record shows it.

## See also
- [Settings](06-03-settings.md)
- [Read the status bar](01-03-the-status-bar.md)
