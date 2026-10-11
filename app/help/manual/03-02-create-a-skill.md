# Create a skill

## Steps

1. Click **+ New skill** (Skills view) or **Catalog** › **New skill…**.
2. Give it a **name** (it cannot change later), a display name and a one-line **description**: what it is for.
3. List the **apps** it is offered to, the **tags**, and the **tools** it expects (comma-separated).
4. Declare its **arguments** as a JSON list: `[{"name": "kb_tool", "description": "…", "required": false, "default": "…"}]`.
5. Write the **content**: the instruction itself. Write `{{kb_tool}}` where an argument goes.
6. Click **Save…**, read the record, click **Save skill**.

## Notes

- Keep the content short and in the imperative: it is read by a model at every turn.
- A required argument without a default makes `prompts/get` refuse a call that does not give it.

## See also
- [What a skill is, and what belongs here](03-01-what-a-skill-is.md)
- [Try a skill](03-03-try-a-skill.md)
