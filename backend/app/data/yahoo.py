"""yfinance-backed market data. Runs blocking calls in a thread."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from app.data import cache


async def _run(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)


async def get_price_history(ticker: str, period: str = "6mo", interval: str = "1d") -> list[dict[str, Any]]:
    key = {"t": ticker, "p": period, "i": interval}
    hit = cache.load("yahoo_hist", key, ttl_seconds=60 * 30)
    if hit is not None:
        return hit

    def _fetch() -> list[dict[str, Any]]:
        df: pd.DataFrame = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return []
        df = df.reset_index()
        df.columns = [str(c).lower() for c in df.columns]
        out = []
        for _, row in df.iterrows():
            d = row.get("date") or row.get("datetime")
            out.append({
                "date": (d.isoformat() if hasattr(d, "isoformat") else str(d)),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
            })
        return out

    data = await _run(_fetch)
    cache.save("yahoo_hist", key, data)
    return data


async def get_quote(ticker: str) -> dict[str, Any]:
    key = {"t": ticker}
    hit = cache.load("yahoo_quote", key, ttl_seconds=60)
    if hit is not None:
        return hit

    def _fetch() -> dict[str, Any]:
        tk = yf.Ticker(ticker)
        fi = tk.fast_info
        info: dict[str, Any] = {}
        try:
            info = tk.info or {}
        except Exception:
            info = {}
        return {
            "ticker": ticker,
            "price": float(fi.last_price) if fi.last_price else None,
            "prev_close": float(fi.previous_close) if fi.previous_close else None,
            "day_high": float(fi.day_high) if fi.day_high else None,
            "day_low": float(fi.day_low) if fi.day_low else None,
            "market_cap": info.get("marketCap"),
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg": info.get("pegRatio"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "name": info.get("shortName") or info.get("longName") or ticker,
            "summary": (info.get("longBusinessSummary") or "")[:1500],
            "fetched_at": datetime.utcnow().isoformat(),
        }

    data = await _run(_fetch)
    cache.save("yahoo_quote", key, data)
    return data


async def get_fundamentals(ticker: str) -> dict[str, Any]:
    key = {"t": ticker}
    hit = cache.load("yahoo_fund", key, ttl_seconds=60 * 60 * 24)
    if hit is not None:
        return hit

    def _fetch() -> dict[str, Any]:
        tk = yf.Ticker(ticker)
        try:
            info = tk.info or {}
        except Exception:
            info = {}
        return {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "free_cashflow": info.get("freeCashflow"),
            "operating_cashflow": info.get("operatingCashflow"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            "target_mean_price": info.get("targetMeanPrice"),
            "target_low_price": info.get("targetLowPrice"),
            "target_high_price": info.get("targetHighPrice"),
            "recommendation_key": info.get("recommendationKey"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "short_percent": info.get("shortPercentOfFloat"),
        }

    data = await _run(_fetch)
    cache.save("yahoo_fund", key, data)
    return data
