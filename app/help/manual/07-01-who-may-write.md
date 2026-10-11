# Who may write

Reads are open on the internal network. Writes (creating, editing, enabling, deleting, keys, restores) and **Try it**
need one of:

- **a signed-in administrator** on the domain: the proxy (Microsoft Entra ID) admits you and names you; the
  service trusts the name only together with the proxy's secret; your address is on the administrator list
  (`MCP_ADMIN_EMAILS`, or anyone the proxy admits when the list is empty). Recorded under your address.
- **the admin token** (`MCP_ADMIN_TOKEN`), pasted in the field at the top right, or sent by a program. Recorded as
  `console`.

A signed-in person who is not an administrator reads everything and may use read-tier tools.

## See also
- [Sign in and out, and switch between the dark and light theme](01-02-sign-in-and-theme.md)
- [The public address](07-04-the-public-address.md)
