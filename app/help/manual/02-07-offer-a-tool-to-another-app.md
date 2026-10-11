# Offer a tool to another app

A tool is defined **once** and offered to the apps in its **apps** list. An app sees a tool, on its MCP endpoint and in
its REST list, only when it is in that list.

## Steps

1. Open the tool and click **Edit**.
2. In **apps**, add the app's name to the comma-separated list (or remove one to withdraw the tool from it).
3. Click **Save…**, check the diff, click **Save tool**.
4. Open **Apps**: the app's card now counts the tool; its *Connect* snippets name the same endpoint as before.

## Notes

- An app that does not exist yet appears as soon as a tool or a skill names it. Give it a key afterwards.
- The tool's description is the same for every app it is offered to.

## See also
- [See what an app is offered](04-01-an-apps-surface.md)
- [Issue a key to an app](04-02-issue-a-key.md)
