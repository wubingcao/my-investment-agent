from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db import session_scope
from app.models import Watchlist
from app.schemas import WatchlistItem

router = APIRouter()


@router.get("")
async def list_watchlist() -> list[dict]:
    async with session_scope() as db:
        rows = (await db.execute(select(Watchlist).order_by(Watchlist.added_at))).scalars().all()
    return [
        {"ticker": r.ticker, "notes": r.notes, "added_at": r.added_at.isoformat()}
        for r in rows
    ]


@router.post("")
async def add_watchlist(item: WatchlistItem) -> dict:
    ticker = item.ticker.upper().strip()
    if not ticker:
        raise HTTPException(400, "ticker required")
    async with session_scope() as db:
        existing = (await db.execute(select(Watchlist).where(Watchlist.ticker == ticker))).scalar_one_or_none()
        if existing:
            existing.notes = item.notes
        else:
            db.add(Watchlist(ticker=ticker, notes=item.notes))
    return {"ok": True, "ticker": ticker}


@router.delete("/{ticker}")
async def remove_watchlist(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    async with session_scope() as db:
        existing = (await db.execute(select(Watchlist).where(Watchlist.ticker == ticker))).scalar_one_or_none()
        if existing:
            await db.delete(existing)
    return {"ok": True}
