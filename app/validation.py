"""Argument validation against a tool's ``input_schema`` (console_specification.md
section 4.3), JSON Schema 2020-12. Returns the error the caller receives, or None."""
from __future__ import annotations

from jsonschema import Draft202012Validator, exceptions


def validate(schema: dict | None, args: dict | None) -> dict | None:
    schema = schema or {"type": "object"}
    try:
        validator = Draft202012Validator(schema)
    except exceptions.SchemaError as e:
        return {"code": "invalid_schema", "message": f"the tool's input_schema is not valid: {e.message}",
                "path": ""}
    errors = sorted(validator.iter_errors(args if args is not None else {}), key=lambda e: list(e.path))
    if not errors:
        return None
    e = errors[0]
    path = "/" + "/".join(str(p) for p in e.absolute_path)
    return {"code": "invalid_arguments", "message": e.message, "path": path}


def schema_error(schema: dict | None) -> str | None:
    """For the editor: why a schema cannot be saved, or None."""
    try:
        Draft202012Validator.check_schema(schema or {})
        return None
    except exceptions.SchemaError as e:
        return e.message
