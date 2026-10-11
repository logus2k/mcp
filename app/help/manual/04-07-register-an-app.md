# Register an app in the catalog

The **application catalog** is the list of consumers of the service: each has a record with a display name, a
description, an **owner**, a **contact**, a **status** and tags. A tool or a skill can only be offered to a registered
app, and a key can only be issued to one. Every change to a record is versioned.

## Steps

1. Click **Apps** in the side menu, then **+ New app**.
2. Give it a **name** (letters, digits, `-` and `_`; it is the app's endpoint, `/mcp/<name>/`, and cannot change),
   a display name, a description, the **owner** (a team or a person) and a **contact**.
3. Click **Save app**. The card appears; it has no tools, skills or keys yet.
4. Offer it tools and skills (their **Edit** tabs list the registered apps as checkboxes), and issue it a key.

## Retire an app

1. Open the app's card, click **Edit**, set **status** to *retired*, click **Save app**.
2. From then on its endpoint and its tools refuse calls, and no key can be issued to it. Its records, keys and
   history stay; set it back to *active* to resume.

## Delete an app

1. Open the card, click **Edit**, then **Delete app**.
2. If the app is still offered tools or skills, or holds active keys, the confirmation says so: deleting then
   withdraws the offers and revokes the keys. The app's history is kept and the record can be restored from it.

## Notes

- An app that a tool or skill names without a record shows as **not registered** on its card and on the Overview;
  **Register** on the card creates the record.
- The apps that existed before the catalog were registered automatically, with a description that says so: give
  them an owner and a contact.

## See also
- [See what an app is offered](04-01-an-apps-surface.md)
- [Issue a key to an app](04-02-issue-a-key.md)
