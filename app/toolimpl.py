"""Built-in tool implementations. The catalog (registry) is declarative; the
executable code lives here. Add a new built-in by writing an async fn and
registering it in IMPLS — never by accepting code from the UI.
"""
from __future__ import annotations

import os

import httpx

WEBSEARCH_URL = os.getenv("WEBSEARCH_URL", "http://websearch_server:8080").rstrip("/")


async def web_search(args: dict, config: dict) -> dict:
    """Delegate to the isolated websearch service (Camoufox stealth browser)."""
    query = (args.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    max_results = int(args.get("max_results") or config.get("max_results") or 5)
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(f"{WEBSEARCH_URL}/search",
                              json={"query": query, "max_results": max_results})
    if r.status_code != 200:
        raise RuntimeError(f"websearch {r.status_code}: {r.text[:200]}")
    return r.json()


IMPLS = {
    "web_search": web_search,
}


async def invoke(impl: str, args: dict, config: dict):
    fn = IMPLS.get(impl)
    if fn is None:
        raise KeyError(f"no built-in implementation '{impl}'")
    return await fn(args or {}, config or {})
