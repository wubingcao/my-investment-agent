"""FRED macro data wrapper. Graceful no-op without key."""
from __future__ import annotations

import asyncio
from typing import Any

from app.config import get_settings
from app.data import cache

MACRO_SERIES = {
    "DFF": "Fed Funds Rate",
    "DGS10": "10Y Treasury Yield",
    "DGS2": "2Y Treasury Yield",
    "T10Y2Y": "10Y - 2Y Spread",
    "CPIAUCSL": "CPI (All Urban)",
    "UNRATE": "Unemployment Rate",
    "GDP": "GDP",
    "DEXUSEU": "USD/EUR",
    "DCOILWTICO": "WTI Crude",
    "VIXCLS": "VIX",
}


async def get_macro_snapshot() -> dict[str, Any]:
    cfg = get_settings()
    if not cfg.fred_api_key:
        return {"available": False, "series": {}}
    hit = cache.load("fred_macro", {"v": 1}, ttl_seconds=60 * 60 * 4)
    if hit is not None:
        return hit

    def _fetch() -> dict[str, Any]:
        from fredapi import Fred
        fred = Fred(api_key=cfg.fred_api_key)
        out = {"available": True, "series": {}}
        for code, name in MACRO_SERIES.items():
            try:
                s = fred.get_series_latest_release(code)
                if s is None or len(s) == 0:
                    continue
                latest = s.dropna()
                if len(latest) == 0:
                    continue
                val = float(latest.iloc[-1])
                prior = float(latest.iloc[-2]) if len(latest) > 1 else val
                out["series"][code] = {
                    "name": name,
                    "latest": val,
                    "prior": prior,
                    "change": val - prior,
                    "pct_change": (val - prior) / prior * 100 if prior else 0,
                }
            except Exception:
                continue
        return out

    data = await asyncio.to_thread(_fetch)
    cache.save("fred_macro", {"v": 1}, data)
    return data
