"""The invocation record (console_specification.md section 4.2): one row per tool call,
on both faces, in SQLite (``activity.db``, WAL). Arguments are kept as a digest; the
JSON itself only for read-tier tools and only when ``MCP_RECORD_ARGS=1``. Rows older
than ``MCP_RETENTION_DAYS`` (90) are pruned once a day.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

from app import registry

_LOCK = threading.RLock()
_last_prune = 0.0

_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
  id TEXT PRIMARY KEY, ts TEXT NOT NULL, app TEXT, tool TEXT, transport TEXT,
  caller TEXT, on_behalf_of TEXT, ok INTEGER, error TEXT, duration_ms INTEGER,
  args_digest TEXT, args_json TEXT, result_chars INTEGER);
CREATE INDEX IF NOT EXISTS calls_ts ON calls(ts);
CREATE INDEX IF NOT EXISTS calls_tool ON calls(tool, ts);
CREATE INDEX IF NOT EXISTS calls_app ON calls(app, ts);
"""

WINDOWS = {"1h": 1, "24h": 24, "7d": 24 * 7, "30d": 24 * 30}


def _path() -> str:
    return os.path.join(registry.data_dir(), "activity.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(registry.data_dir(), exist_ok=True)
    c = sqlite3.connect(_path(), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def record_args() -> bool:
    return os.getenv("MCP_RECORD_ARGS", "0") == "1"


def retention_days() -> int:
    try:
        return max(1, int(os.getenv("MCP_RETENTION_DAYS", "90")))
    except ValueError:
        return 90


def record(*, app: str | None, tool: str, transport: str, caller: str, on_behalf_of: str | None,
           ok: bool, error: str | None, duration_ms: int, args: dict | None, tier: str,
           result_chars: int | None) -> str:
    canonical = json.dumps(args or {}, sort_keys=True, ensure_ascii=False)
    row = {
        "id": uuid.uuid4().hex, "ts": _now().isoformat(), "app": app or "", "tool": tool,
        "transport": transport, "caller": caller, "on_behalf_of": on_behalf_of or "",
        "ok": 1 if ok else 0, "error": (error or "")[:1000], "duration_ms": int(duration_ms),
        "args_digest": hashlib.sha256(canonical.encode()).hexdigest(),
        "args_json": canonical if (record_args() and tier == "read") else None,
        "result_chars": result_chars,
    }
    with _LOCK:
        c = _connect()
        try:
            c.execute("INSERT INTO calls VALUES (:id,:ts,:app,:tool,:transport,:caller,:on_behalf_of,"
                      ":ok,:error,:duration_ms,:args_digest,:args_json,:result_chars)", row)
            c.commit()
        finally:
            c.close()
    _maybe_prune()
    return row["id"]


def _maybe_prune() -> None:
    global _last_prune
    if time.monotonic() - _last_prune < 24 * 3600:
        return
    _last_prune = time.monotonic()
    prune()


def prune(days: int | None = None) -> int:
    cutoff = (_now() - timedelta(days=days or retention_days())).isoformat()
    with _LOCK:
        c = _connect()
        try:
            n = c.execute("DELETE FROM calls WHERE ts < ?", (cutoff,)).rowcount
            c.commit()
            return n
        finally:
            c.close()


def _since(window: str | None, since: str | None) -> str | None:
    if since:
        return since
    hours = WINDOWS.get(window or "", None)
    return (_now() - timedelta(hours=hours)).isoformat() if hours else None


def _where(app=None, tool=None, caller=None, ok=None, since=None, until=None, on_behalf_of=None,
           transport=None, q=None) -> tuple[str, list]:
    clauses, params = [], []
    for col, val in (("app", app), ("tool", tool), ("caller", caller), ("on_behalf_of", on_behalf_of),
                     ("transport", transport)):
        if val:
            clauses.append(f"{col} = ?")
            params.append(val)
    if ok is not None:
        clauses.append("ok = ?")
        params.append(1 if ok else 0)
    if since:
        clauses.append("ts >= ?")
        params.append(since)
    if until:
        clauses.append("ts <= ?")
        params.append(until)
    if q:
        clauses.append("(error LIKE ? OR tool LIKE ? OR caller LIKE ? OR on_behalf_of LIKE ?)")
        params += [f"%{q}%"] * 4
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def query(*, limit: int = 100, cursor: str | None = None, window: str | None = None, since=None,
          **filters) -> dict:
    """Newest first. ``cursor`` is the ``ts`` of the last row seen."""
    where, params = _where(since=_since(window, since), **filters)
    if cursor:
        where += (" AND " if where else " WHERE ") + "ts < ?"
        params.append(cursor)
    limit = max(1, min(int(limit), 1000))
    with _LOCK:
        c = _connect()
        try:
            rows = [dict(r) for r in c.execute(
                f"SELECT * FROM calls{where} ORDER BY ts DESC LIMIT ?", params + [limit + 1])]
        finally:
            c.close()
    more = len(rows) > limit
    rows = rows[:limit]
    for r in rows:
        r["ok"] = bool(r["ok"])
    return {"calls": rows, "next_cursor": rows[-1]["ts"] if more and rows else None}


def _percentile(values: list[int], p: float) -> int | None:
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, max(0, round(p * (len(values) - 1))))
    return values[idx]


def summary(window: str = "24h", app: str | None = None) -> dict:
    """Per tool: calls, errors, p50/p95 duration, last used; plus totals."""
    since = _since(window, None)
    where, params = _where(app=app, since=since)
    with _LOCK:
        c = _connect()
        try:
            rows = c.execute(f"SELECT tool, app, ok, duration_ms, ts FROM calls{where}", params).fetchall()
            last_any = {r["tool"]: r["ts"] for r in c.execute(
                "SELECT tool, MAX(ts) AS ts FROM calls GROUP BY tool")}
        finally:
            c.close()
    per: dict[str, dict] = {}
    for r in rows:
        t = per.setdefault(r["tool"], {"tool": r["tool"], "calls": 0, "errors": 0, "durations": [],
                                       "last_used": None, "apps": set()})
        t["calls"] += 1
        t["errors"] += 0 if r["ok"] else 1
        t["durations"].append(r["duration_ms"])
        t["apps"].add(r["app"])
        if not t["last_used"] or r["ts"] > t["last_used"]:
            t["last_used"] = r["ts"]
    tools = []
    for t in per.values():
        tools.append({"tool": t["tool"], "calls": t["calls"], "errors": t["errors"],
                      "p50_ms": _percentile(t["durations"], 0.5), "p95_ms": _percentile(t["durations"], 0.95),
                      "last_used": t["last_used"], "apps": sorted(t["apps"])})
    tools.sort(key=lambda x: -x["calls"])
    all_durations = [r["duration_ms"] for r in rows]
    return {
        "window": window, "since": since, "app": app,
        "calls": len(rows), "errors": sum(1 for r in rows if not r["ok"]),
        "p50_ms": _percentile(all_durations, 0.5), "p95_ms": _percentile(all_durations, 0.95),
        "tools": tools,
        "last_used": last_any,  # every tool ever called, regardless of window
    }


def to_csv(**filters) -> str:
    rows = query(limit=1000, **filters)["calls"]
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["ts", "app", "tool", "transport", "caller", "on_behalf_of", "ok", "error", "duration_ms",
            "args_digest", "result_chars"]
    w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c) for c in cols])
    return buf.getvalue()
