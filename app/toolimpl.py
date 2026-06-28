"""Built-in tool implementations. The catalog (registry) is declarative; the
executable code lives here. Add a new built-in by writing an async fn and
registering it in IMPLS — never by accepting code from the UI.
"""
from __future__ import annotations

import html as _html
import os
import re

import httpx

WEBSEARCH_URL = os.getenv("WEBSEARCH_URL", "http://websearch_server:8080").rstrip("/")

_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANKLINES_RE = re.compile(r"\n\s*\n+")


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


async def fetch_url(args: dict, config: dict) -> str:
    """Fetch a web URL and return its readable text (HTML stripped)."""
    url = (args.get("url") or "").strip()
    if not url:
        raise ValueError("url is required")
    max_chars = int(args.get("max_chars") or config.get("max_chars") or 10000)
    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (mcp-service fetch_url)"},
    ) as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"fetch_url {r.status_code} for {url}: {r.text[:200]}")
    text = _SCRIPT_RE.sub(" ", r.text)
    text = _TAG_RE.sub(" ", text)
    text = _html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text).strip()
    return text[:max_chars]


async def newsapi_search(args: dict, config: dict) -> str:
    """Search NewsAPI for recent articles. Key from config['api_key'] or env
    NEWSAPI_KEY (kept out of the registry/source — env only)."""
    query = (args.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    key = config.get("api_key") or os.getenv("NEWSAPI_KEY") or ""
    if not key:
        raise RuntimeError("NEWSAPI_KEY is not configured (set it in the environment)")
    page_size = int(args.get("page_size") or config.get("page_size") or 20)
    sort_by = args.get("sort_by") or config.get("sort_by") or "relevancy"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": page_size,
                    "sortBy": sort_by, "language": "en"},
            headers={"X-Api-Key": key},
        )
    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(f"NewsAPI error: {data.get('message') or data}")
    # Dedupe by URL (and by title) — NewsAPI returns syndicated duplicates.
    seen: set[str] = set()
    lines = [f"NewsAPI results for {query!r} ({data.get('totalResults', 0)} total):", ""]
    n = 0
    for a in data.get("articles", []):
        url = a.get("url") or ""
        title = (a.get("title") or "").strip()
        key_ = url or title
        if not key_ or key_ in seen:
            continue
        seen.add(key_)
        n += 1
        src = (a.get("source") or {}).get("name") or ""
        lines.append(f"{n}. {title} — {url} ({src})")
    return "\n".join(lines)


IMPLS = {
    "web_search": web_search,
    "fetch_url": fetch_url,
    "newsapi_search": newsapi_search,
}


async def invoke(impl: str, args: dict, config: dict):
    fn = IMPLS.get(impl)
    if fn is None:
        raise KeyError(f"no built-in implementation '{impl}'")
    return await fn(args or {}, config or {})
