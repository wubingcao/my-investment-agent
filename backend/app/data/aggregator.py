"""Composes all data sources into a single per-ticker research brief."""
from __future__ import annotations

import asyncio
from typing import Any

from app.data import yahoo, finnhub, newsapi, fred, technical


async def build_research_brief(ticker: str) -> dict[str, Any]:
    """Gather everything an expert persona needs to reason about a ticker."""
    quote_t = yahoo.get_quote(ticker)
    fund_t = yahoo.get_fundamentals(ticker)
    hist_t = yahoo.get_price_history(ticker, period="1y", interval="1d")
    intraday_t = yahoo.get_price_history(ticker, period="5d", interval="60m")
    news_t = finnhub.company_news(ticker, days=7)
    earnings_t = finnhub.earnings_calendar(ticker, days_ahead=60)
    market_news_t = newsapi.top_headlines(query=ticker, page_size=10)

    quote, fund, hist, intraday, news, earnings, mkt_news = await asyncio.gather(
        quote_t, fund_t, hist_t, intraday_t, news_t, earnings_t, market_news_t,
        return_exceptions=True,
    )

    def _ok(x, default):
        return x if not isinstance(x, Exception) else default

    quote = _ok(quote, {})
    fund = _ok(fund, {})
    hist = _ok(hist, [])
    intraday = _ok(intraday, [])
    news = _ok(news, [])
    earnings = _ok(earnings, [])
    mkt_news = _ok(mkt_news, [])

    indicators_daily = technical.compute_indicators(hist)
    indicators_intraday = technical.compute_indicators(intraday)

    return {
        "ticker": ticker,
        "quote": quote,
        "fundamentals": fund,
        "indicators_daily": indicators_daily,
        "indicators_intraday": indicators_intraday,
        "recent_bars_daily": hist[-60:],       # last ~60 days
        "recent_bars_intraday": intraday[-40:],
        "company_news": news,
        "market_news": mkt_news,
        "earnings_calendar": earnings,
    }


async def build_macro_context() -> dict[str, Any]:
    macro = await fred.get_macro_snapshot()
    return {"macro": macro}
