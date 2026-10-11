# See what an app is offered

An **app** is a consumer of the service: an application (Cortex, job2cool, the SDLC wall) or an agent. Each has a
record in the **application catalog** (owner, contact, status), its own MCP endpoint, `/mcp/<app>/`, its own REST
list, `/tools?app=<app>`, and sees only the tools and skills offered to it.

## Steps

1. Click **Apps** in the side menu. One card per app: its record (display name, description, owner, contact,
   status), its endpoint, how many tools and skills it is offered, its calls in the last 24 hours, and its **keys**.
2. Click the tools count to open **Tools** filtered by that app.
3. Click **Connect** for the snippets that connect a program or an MCP client as this app.

## Notes

- **Apps** in the top menu lists the same apps with their tools and keys; an entry opens the card.
- An app without a key is flagged on the Overview: its calls are recorded as *anonymous*.
- **Edit** opens the record; **Register** appears on a card whose name a tool or skill uses without a record.

## See also
- [Register an app in the catalog](04-07-register-an-app.md)
- [Issue a key to an app](04-02-issue-a-key.md)
- [Connect an application](04-04-connect-an-app.md)
