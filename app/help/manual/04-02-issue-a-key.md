# Issue a key to an app

A **key** identifies the caller. It is bound to one app, it is shown **once**, and the service keeps only its
fingerprint. A write-tier tool always needs a key (or an administrator); a read-tier tool needs one when keys are
required.

## Steps

1. Open **Apps** and find the app's card.
2. Under **Keys**, name the key after the program that will hold it (*cortex-learning*, *daily-digest*), choose when
   it expires (90, 180 or 365 days), and click **+ New key**.
3. The key appears once, highlighted: click **Copy** and store it where that program keeps its secrets.
4. Give it to the program: see [Connect an application](04-04-connect-an-app.md).

![An app's card with a key just issued](img/04-02-issue-a-key-1.png)

## Notes

- A key looks like `mcpk_` followed by 43 characters.
- An app may have up to 20 active keys: one per program, so each can be revoked alone.
- The list shows each key's name, id, dates and last use; never the key itself.

## See also
- [Revoke or rotate a key](04-03-revoke-or-rotate-a-key.md)
- [Require keys from every caller](07-02-require-keys.md)
