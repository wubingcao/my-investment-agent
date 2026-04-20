from fastapi import APIRouter, HTTPException
from sqlalchemy import select, desc

from app.data import yahoo
from app.data.technical import compute_indicators
from app.db import session_scope
from app.models import Signal

router = APIRouter()


@router.get("/latest")
async def latest_signals(limit: int = 50) -> list[dict]:
    async with session_scope() as db:
        stmt = select(Signal).order_by(desc(Signal.created_at)).limit(limit)
        rows = (await db.execute(stmt)).scalars().all()
    return [_signal_out(s) for s in rows]


@router.get("/by-ticker/{ticker}")
async def signal_by_ticker(ticker: str, limit: int = 20) -> list[dict]:
    ticker = ticker.upper().strip()
    async with session_scope() as db:
        stmt = (
            select(Signal)
            .where(Signal.ticker == ticker)
            .order_by(desc(Signal.created_at))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
    return [_signal_out(s) for s in rows]


@router.get("/{signal_id}")
async def signal_detail(signal_id: int) -> dict:
    async with session_scope() as db:
        row = await db.get(Signal, signal_id)
        if not row:
            raise HTTPException(404, "signal not found")
    return _signal_out(row, include_raw=True)


@router.get("/{signal_id}/chart")
async def signal_chart(signal_id: int, period: str = "6mo", interval: str = "1d") -> dict:
    """Candle data + indicators for the signal's ticker, formatted for Lightweight Charts."""
    async with session_scope() as db:
        row = await db.get(Signal, signal_id)
        if not row:
            raise HTTPException(404, "signal not found")
    bars = await yahoo.get_price_history(row.ticker, period=period, interval=interval)
    indicators = compute_indicators(bars)
    return {
        "ticker": row.ticker,
        "period": period,
        "interval": interval,
        "bars": bars,
        "indicators": indicators,
        "signal": _signal_out(row),
    }


def _signal_out(s: Signal, include_raw: bool = False) -> dict:
    out = {
        "id": s.id,
        "run_id": s.run_id,
        "ticker": s.ticker,
        "action": s.action,
        "confidence": s.confidence,
        "buy_low": s.buy_low,
        "buy_high": s.buy_high,
        "sell_low": s.sell_low,
        "sell_high": s.sell_high,
        "stop_loss": s.stop_loss,
        "target_pct": s.target_pct,
        "time_horizon": s.time_horizon,
        "summary": s.summary or "",
        "thesis": s.thesis,
        "risks": s.risks,
        "debate_summary": s.debate_summary,
        "qc_passed": s.qc_passed,
        "qc_notes": s.qc_notes,
        "created_at": s.created_at.isoformat(),
    }
    if include_raw:
        out["experts"] = (s.raw or {}).get("experts", [])
        out["debate"] = (s.raw or {}).get("debate", [])
        out["qc"] = (s.raw or {}).get("qc", {})
        out["brief_snapshot"] = (s.raw or {}).get("brief_snapshot", {})
    return out
