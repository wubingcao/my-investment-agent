"""Evaluate emitted signals against subsequent price action.

For each signal older than `min_age_days` and without an outcome, fetch the
price history from the signal date forward and score it:
- entry: midpoint of buy_low/buy_high (or current close if not provided)
- hit_target: price touched sell_high (or exit midpoint) within horizon_days
- hit_stop:   price touched stop_loss within horizon_days
- pnl_pct:    (exit_price - entry) / entry for longs, flipped for shorts
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, and_, not_

from app.data import yahoo
from app.db import session_scope
from app.models import Signal, SignalOutcome

log = logging.getLogger(__name__)

HORIZON_DAYS = {"day": 2, "swing": 7, "position": 30}


async def run_daily_evaluation(min_age_days: int = 2) -> dict[str, Any]:
    cutoff = datetime.utcnow() - timedelta(days=min_age_days)
    scored = 0
    skipped = 0
    async with session_scope() as db:
        # signals older than cutoff without an outcome
        stmt = select(Signal).where(Signal.created_at <= cutoff).order_by(Signal.created_at.desc()).limit(200)
        candidates = (await db.execute(stmt)).scalars().all()
        existing_outcomes = (
            await db.execute(select(SignalOutcome.signal_id))
        ).scalars().all()
        have = set(existing_outcomes)

    for sig in candidates:
        if sig.id in have:
            continue
        if sig.action == "HOLD":
            continue

        horizon_days = HORIZON_DAYS.get(sig.time_horizon, 7)
        bars = await yahoo.get_price_history(sig.ticker, period="3mo", interval="1d")
        outcome = _score(sig, bars, horizon_days)
        if outcome is None:
            skipped += 1
            continue

        async with session_scope() as db:
            db.add(SignalOutcome(
                signal_id=sig.id,
                horizon_days=horizon_days,
                entry_price=outcome["entry_price"],
                exit_price=outcome["exit_price"],
                pnl_pct=outcome["pnl_pct"],
                hit_target=outcome["hit_target"],
                hit_stop=outcome["hit_stop"],
                notes=outcome["notes"],
            ))
        scored += 1

    log.info("Performance eval: scored=%d skipped=%d", scored, skipped)
    return {"scored": scored, "skipped": skipped}


def _score(sig: Signal, bars: list[dict[str, Any]], horizon_days: int) -> dict[str, Any] | None:
    if not bars:
        return None
    sig_dt = sig.created_at.date()
    forward = [b for b in bars if b["date"][:10] > sig_dt.isoformat()][:horizon_days]
    if not forward:
        return None

    entry = None
    if sig.buy_low is not None and sig.buy_high is not None:
        entry = (sig.buy_low + sig.buy_high) / 2
    else:
        # use first forward open as best-guess entry
        entry = forward[0]["open"]
    if not entry:
        return None

    direction = 1 if sig.action == "BUY" else -1

    target = None
    if sig.sell_low is not None and sig.sell_high is not None:
        target = (sig.sell_low + sig.sell_high) / 2
    stop = sig.stop_loss

    exit_price = forward[-1]["close"]
    hit_target = False
    hit_stop = False
    for b in forward:
        if direction > 0:
            if stop is not None and b["low"] <= stop:
                exit_price = stop
                hit_stop = True
                break
            if target is not None and b["high"] >= target:
                exit_price = target
                hit_target = True
                break
        else:
            if stop is not None and b["high"] >= stop:
                exit_price = stop
                hit_stop = True
                break
            if target is not None and b["low"] <= target:
                exit_price = target
                hit_target = True
                break

    pnl_pct = direction * (exit_price - entry) / entry * 100
    return {
        "entry_price": round(entry, 4),
        "exit_price": round(exit_price, 4),
        "pnl_pct": round(pnl_pct, 3),
        "hit_target": hit_target,
        "hit_stop": hit_stop,
        "notes": f"{sig.action} graded over {len(forward)} bars; target={hit_target} stop={hit_stop}",
    }
