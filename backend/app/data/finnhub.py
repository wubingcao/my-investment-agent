"""Finnhub free-tier wrapper. Gracefully no-ops when no API key is set."""
from __future__ import annotations

import asyncio
from typing import Any

from app.config import get_settings
from app.data import cache


def _client():
    import finnhub
    return finnhub.Client(api_key=get_settings().finnhub_api_key)


async def company_news(ticker: str, days: int = 7) -> list[dict[str, Any]]:
    cfg = get_settings()
    if not cfg.finnhub_api_key:
        return []
    key = {"t": ticker, "d": days}
    hit = cache.load("finnhub_news", key, ttl_seconds=60 * 60)
    if hit is not None:
        return hit

    from datetime import date, timedelta
    to = date.today()
    frm = to - timedelta(days=days)

    def _fetch():
        try:
            c = _client()
            return c.company_news(ticker, _from=frm.isoformat(), to=to.isoformat()) or []
        except Exception:
            return []

    items = await asyncio.to_thread(_fetch)
    trimmed = [
        {
            "datetime": it.get("datetime"),
            "headline": it.get("headline"),
            "summary": (it.get("summary") or "")[:800],
            "source": it.get("source"),
            "url": it.get("url"),
            "category": it.get("category"),
        }
        for it in items[:25]
    ]
    cache.save("finnhub_news", key, trimmed)
    return trimmed


async def earnings_calendar(ticker: str, days_ahead: int = 60) -> list[dict[str, Any]]:
    cfg = get_settings()
    if not cfg.finnhub_api_key:
        return []
    key = {"t": ticker, "d": days_ahead}
    hit = cache.load("finnhub_earn", key, ttl_seconds=60 * 60 * 6)
    if hit is not None:
        return hit

    from datetime import date, timedelta
    frm = date.today()
    to = frm + timedelta(days=days_ahead)

    def _fetch():
        try:
            c = _client()
            r = c.earnings_calendar(_from=frm.isoformat(), to=to.isoformat(), symbol=ticker) or {}
            return r.get("earningsCalendar", [])
        except Exception:
            return []

    data = await asyncio.to_thread(_fetch)
    cache.save("finnhub_earn", key, data)
    return data
