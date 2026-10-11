# The public address

On the domain the console is at `https://logus2k.com/mcp-console/admin`, behind the proxy's Microsoft Entra ID
sign-in, for the administrators only. The REST face is under the same prefix and the same gate.

Applications and agents do not use that address: they connect on the **internal network**, at
`http://mcp-service:8080`, with their keys. The MCP endpoint is `/mcp/<app>/` there.

## See also
- [Connect an application](04-04-connect-an-app.md)
- [Who may write](07-01-who-may-write.md)
