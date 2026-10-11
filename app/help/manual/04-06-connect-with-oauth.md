# Connect an MCP client with OAuth

Claude Code, claude.ai's custom connectors and other MCP clients can sign a **person** in instead of holding a key:
the client discovers the service's OAuth server, Microsoft signs the person in through the domain, a consent page asks
what the client may do, and the person allows it. Every call is then recorded under their address.

## Steps

1. Give the client the app's public endpoint: `https://logus2k.com/mcp-console/mcp/<app>/` (the **OAuth 2.1**
   snippet in any tool's **Connect** tab, or an app's **Connect** button).
2. The client opens the sign-in. Sign in with your Microsoft account.
3. The consent page names the client and lists what it asks for: read-tier tools, write-tier tools, administration.
   Click **Allow** (or **Deny**).
4. The client is connected. Open **Activity**: its calls appear as `oauth:<your address>`.

## Notes

- Write-tier tools and administration over OAuth are for people on the administrator list; a client may ask for
  them, the list decides.
- **Settings › OAuth clients** lists the clients that registered; **Remove** ends one's access.
- Inside the network, programs keep using keys: OAuth is for people's clients on the domain.

## See also
- [Connect an agent or Claude](04-05-connect-an-agent.md)
- [Issue a key to an app](04-02-issue-a-key.md)
