# Try a tool

**Try it** runs a tool from the console, with a form built from its schema, and shows exactly what a caller would get.
The call is recorded like any other, under your name.

## Steps

1. Open the tool and click **Try it**.
2. Choose the **app** the call is for, when the tool is offered to several.
3. Fill the arguments: a text field, a number, a true/false choice or a list of values, as the schema says. A required
   argument has a `*`.
4. For a **write** tool, tick the confirmation: it says what the tool changes and against which app.
5. Click **Run**. The result appears below with the status, how long it took, and who it was recorded as.
6. **Copy as curl** puts the same call on the clipboard, ready for a terminal.

![A tool's Try it tab: the form, the Run button and the result](img/02-03-try-a-tool-1.png)

## Notes

- On the domain, Try it runs as you. On the service's port, paste the admin token first: Try it then runs as the
  console.
- A *client* tool cannot be run here: the app's own page executes it.
- A disabled tool cannot be run; enable it first.

## See also
- [Read a tool's schema](02-02-read-a-tools-schema.md)
- [See a tool's calls](02-08-see-a-tools-calls.md)
