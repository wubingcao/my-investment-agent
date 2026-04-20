"""NewsAPI.org free-tier wrapper. Broad market/macro news."""
from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.data import cache


async def top_headlines(query: str, page_size: int = 20) -> list[dict[str, Any]]:
    cfg = get_settings()
    if not cfg.newsapi_api_key:
        return []
    key = {"q": query, "n": page_size}
    hit = cache.load("newsapi", key, ttl_seconds=60 * 30)
    if hit is not None:
        return hit

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": cfg.newsapi_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            articles = r.json().get("articles", [])
    except Exception:
        return []

    trimmed = [
        {
            "publishedAt": a.get("publishedAt"),
            "title": a.get("title"),
            "description": (a.get("description") or "")[:500],
            "source": (a.get("source") or {}).get("name"),
            "url": a.get("url"),
        }
        for a in articles
    ]
    cache.save("newsapi", key, trimmed)
    return trimmed
