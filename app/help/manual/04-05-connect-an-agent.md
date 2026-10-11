# Connect an agent or Claude

An agent connects over **MCP**: the standard endpoint `/mcp/<app>/` (Streamable HTTP). It discovers the app's tools
with their annotations, calls them, and receives the app's skills as prompts and resources. Claude Code and Claude
Desktop are MCP clients.

## Steps

1. Issue the app a key.
2. Open **Apps** › **Connect** (or a tool's **Connect** tab) and copy the **Claude Code** command or the
   **Claude Desktop** configuration. Paste the key in the console's token field first and the snippets carry it.
3. Run the command (Claude Code) or add the configuration (Claude Desktop). The app's tools appear in the client; its
   skills appear as prompts.
4. Open **Activity**: the agent's calls appear with the key's id.

## Notes

- One key per agent, named after it, so it can be revoked alone.
- An agent that acts for a person should send `X-On-Behalf-Of`; one that acts for nobody is recorded without a
  person.

## See also
- [Issue a key to an app](04-02-issue-a-key.md)
- [What a skill is, and what belongs here](03-01-what-a-skill-is.md)
