# Export and import the registry

The **registry** is the catalog of tools and skills. Export it to keep a copy or to carry a tool to another
installation; import a copy with a dry run first.

## Export

- **Catalog** › **Export the registry** (or Settings › **Registry JSON**): everything, as JSON.
- Filter **Tools** by an app, then **Catalog** › **Export the <app> app**: that app's slice.

## Import (dry run)

1. **Catalog** › **Import (dry run)…**, or Settings › **Import (dry run)** and choose the JSON file.
2. The page lists what the file would **create** and what it would **update**, with the diff of each update. Nothing
   is changed yet.
3. Click **Apply n change(s)** to save them, each as a new version.

## Notes

- Keys and the activity are not part of the registry.
- Names are the identity: a record in the file with an existing name updates it.

## See also
- [Settings](06-03-settings.md)
