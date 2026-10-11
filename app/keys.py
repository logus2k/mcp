"""App keys: who is calling (console_specification.md section 4.1).

A key is ``mcpk_`` + 43 URL-safe characters, bound to exactly one app. The plaintext is
returned once at creation; only its SHA-256 fingerprint is stored (``keys.json``).
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone

from app import registry

PREFIX = "mcpk_"
MAX_ACTIVE_PER_APP = 20
_LOCK = threading.RLock()


def _path() -> str:
    return os.path.join(registry.data_dir(), "keys.json")


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _load() -> dict:
    return registry._read_json(_path(), {})


def _save(data: dict) -> None:
    registry._write_json(_path(), data)


def fingerprint(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def public(rec: dict) -> dict:
    """What lists and the console see: never the fingerprint, never the key."""
    return {k: v for k, v in rec.items() if k != "fingerprint"}


def create(app: str, name: str, expires_days: int = 90) -> tuple[str, dict]:
    app = (app or "").strip()
    if not app:
        raise ValueError("app is required")
    rec = registry.get_app(app)
    if not rec:
        raise ValueError(f"'{app}' is not a registered app: register it first (Apps › New app)")
    if rec.get("status") == "retired":
        raise ValueError(f"'{app}' is retired: no new keys")
    expires_days = max(1, min(int(expires_days or 90), 365))
    with _LOCK:
        data = _load()
        active = [k for k in data.values() if k["app"] == app and not k.get("revoked_at")
                  and k["expires_at"] > _now().isoformat()]
        if len(active) >= MAX_ACTIVE_PER_APP:
            raise ValueError(f"{app} already has {MAX_ACTIVE_PER_APP} active keys; revoke one first")
        plaintext = PREFIX + secrets.token_urlsafe(32)
        rec = {
            "id": secrets.token_hex(6),
            "app": app,
            "name": (name or "").strip() or app,
            "fingerprint": fingerprint(plaintext),
            "created_at": _now().isoformat(),
            "expires_at": (_now() + timedelta(days=expires_days)).isoformat(),
            "last_used_at": None,
            "revoked_at": None,
        }
        data[rec["id"]] = rec
        _save(data)
        return plaintext, public(rec)


def list_keys(app: str | None = None) -> list[dict]:
    return [public(k) for k in _load().values() if app is None or k["app"] == app]


def revoke(key_id: str) -> bool:
    with _LOCK:
        data = _load()
        rec = data.get(key_id)
        if not rec or rec.get("revoked_at"):
            return False
        rec["revoked_at"] = _now().isoformat()
        _save(data)
        return True


def verify(plaintext: str | None) -> dict | None:
    """The key record for a presented key, or None when it is unknown, revoked or
    expired. Records the use."""
    if not plaintext or not plaintext.startswith(PREFIX):
        return None
    fp = fingerprint(plaintext)
    with _LOCK:
        data = _load()
        for rec in data.values():
            if rec["fingerprint"] != fp:
                continue
            if rec.get("revoked_at") or rec["expires_at"] <= _now().isoformat():
                return None
            rec["last_used_at"] = _now().isoformat()
            _save(data)
            return public(rec)
    return None
