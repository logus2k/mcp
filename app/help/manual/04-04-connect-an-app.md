# Connect an application

An application calls tools over **REST** (`POST /tools/<name>/invoke?app=<app>`) with its key, and names the person it
acts for in `X-On-Behalf-Of`. The **Connect** tab of any tool, and the **Connect** button of any app, give the
snippets with the right addresses.

## Steps

1. Issue the app a key.
2. Open the tool the app will call, click **Connect**, and copy the **curl** or **Python** snippet.
3. In the program, send the key as `Authorization: Bearer mcpk_…` and the person's address as `X-On-Behalf-Of`.
4. Make a call and open **Activity**: it appears with the key's id as the caller and the address as *on behalf of*.

## Notes

- The REST list of what the app is offered: `GET /tools?app=<app>`; the model-facing specs: `GET /tools/manifest?app=<app>`.
- Inside the network the address is the service's own (`http://mcp-service:8080`); on the domain, under the
  administrator-only path.
- The full reference is the **Integration Guide** (Help menu).

## See also
- [Connect an agent or Claude](04-05-connect-an-agent.md)
- [Understand a call's record](05-03-understand-a-call.md)
