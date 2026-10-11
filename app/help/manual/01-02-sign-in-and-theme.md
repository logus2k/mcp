# Sign in and out, and switch between the dark and light theme

On the domain, the console is at **https://logus2k.com/mcp-console/admin**. Sign-in is Microsoft Entra ID's, through
the domain's proxy, as for Cortex and Slides: only the administrators on the proxy's list reach the page. Your name
and photo come from your Microsoft account.

## Steps

1. Open the console's address. If you are not signed in, Microsoft asks you to; afterwards the console opens.
2. Your name is at the top right, with your photo (or your initials). Click it: the menu shows your address and
   whether you are an **administrator**.
3. **Dark theme** / **Light theme** in that menu switches the look; the choice is remembered on this browser. The
   same switch is in the side menu's **Settings** and in **View**.
4. **Português** / **English** in that menu switches the interface's language; the page reloads into it, and the
   manual opens in the same language.
5. **Sign out** ends the Microsoft session and brings you back to the sign-in.

## Notes

- Everything you change is recorded under your address: the history of a record, and every call you make with
  *Try it*.
- On the service's own port (inside the network), there is no sign-in. Writes then need the **admin token** pasted
  in the field at the top right; it stays in this browser tab only.
- An administrator is someone the proxy admits whose address is on the service's administrator list. Someone the proxy
  admits who is not on the list can read everything and use read-tier tools, not change anything.

## See also
- [Who may write](07-01-who-may-write.md)
- [The public address](07-04-the-public-address.md)
