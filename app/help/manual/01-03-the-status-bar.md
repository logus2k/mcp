# Read the status bar

The bar along the bottom tells you, from left to right, **which service** this is, **which view** you are in, and the
facts about that view. What concerns the whole service stays at the right.

## What it shows

- **The service** (red, at the left end) — `mcp-service` and its version.
- **The view** (in bold) — Overview, Tools, Skills, Apps, Activity, Settings or Help.
- **Its details**, which depend on the view:

  | The view | Details |
  |---|---|
  | Overview | calls in the last 24 hours, errors |
  | Tools | enabled tools out of all, the app filter or the number of apps, the tier filter, the text filter |
  | Skills | skills, enabled |
  | Apps | apps, active keys |
  | Activity | the window, the app filter |
  | Settings | implementations, orphans |
  | Help | the manual and the page |

- **At the right** — the **backends** (a green dot and *n ok*, or how many are down; click it for Settings), the
  **keys** mode (*optional* or *required*), the **record** (digests or arguments, and the days kept), and the
  **connection** to the service (green when the last health check answered).

## Notes

- Hover a detail to see what it is.
- A phone does not show the status bar.

## See also
- [What MCP Server is, and how the screen is laid out](01-01-the-screen.md)
- [Monitor the backends](06-02-monitor-the-backends.md)
