# Give a program a machine client

A **machine client** is the OAuth way to identify a program that speaks for an app (a daemon, a backend, a scheduled
job): instead of a key, it holds an id and a secret and exchanges them for a token that expires after an hour and
carries explicit scopes (the *client credentials* grant). Nobody signs in: the token acts as the app.

## Steps

1. Open **Apps** and find the app's card.
2. Under **Machine clients**, name the client after the program that will hold it, tick **tools:write** if it must
   use write-tier tools, and click **+ New machine client**.
3. The id and the secret appear once: copy both into the program's secrets.
4. In the program: `POST /oauth/token` with `grant_type=client_credentials`, the id and the secret; send the
   returned token as `Authorization: Bearer …` on the app's endpoint; ask again when it expires.
5. Open **Activity**: the program's calls appear as `client:<id>` for the app, with no person.

## Notes

- A machine client works on its app's endpoint only; a retired app's clients get no token.
- **Remove** on the card ends the client's tokens at once. **Settings › OAuth clients** lists every client, people's
  and machines'.
- A key does the same job without expiry; keep keys for programs that cannot run an OAuth exchange.

## See also
- [Issue a key to an app](04-02-issue-a-key.md)
- [Connect an MCP client with OAuth](04-06-connect-with-oauth.md)
