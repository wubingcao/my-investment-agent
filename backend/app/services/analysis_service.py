from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.agents import orchestrator
from app.data import aggregator
from app.db import session_scope
from app.models import AnalysisRun, Signal
from app.services.settings_service import get_risk_settings
from app.services.pine_script_service import write_pine_script

log = logging.getLogger(__name__)


async def run_analysis(tickers: list[str], horizon: str, trigger: str = "on_demand") -> int:
    tickers = [t.upper().strip() for t in tickers if t.strip()]
    if not tickers:
        raise ValueError("No tickers provided")

    async with session_scope() as db:
        run = AnalysisRun(trigger=trigger, tickers=tickers, status="running")
        db.add(run)
        await db.flush()
        run_id = run.id

    risk = await get_risk_settings()
    macro = (await aggregator.build_macro_context())["macro"]

    portfolio_snapshot = await _current_portfolio_snapshot()

    # Analyze tickers in parallel (bounded concurrency)
    sem = asyncio.Semaphore(4)

    async def _one(t: str) -> dict[str, Any]:
        async with sem:
            try:
                return await orchestrator.analyze_ticker(
                    ticker=t,
                    horizon=horizon,
                    risk_settings=risk.model_dump(),
                    macro=macro,
                    portfolio_snapshot=portfolio_snapshot,
                )
            except Exception as e:
                log.exception("Analysis failed for %s", t)
                return {"ticker": t, "error": str(e)}

    results = await asyncio.gather(*(_one(t) for t in tickers))

    # Persist
    async with session_scope() as db:
        for res in results:
            if "error" in res:
                continue
            sig = res["signal"]
            row = Signal(
                run_id=run_id,
                ticker=res["ticker"],
                action=sig.get("action", "HOLD"),
                confidence=float(sig.get("confidence", 0)),
                buy_low=sig.get("buy_low"),
                buy_high=sig.get("buy_high"),
                sell_low=sig.get("sell_low"),
                sell_high=sig.get("sell_high"),
                stop_loss=sig.get("stop_loss"),
                target_pct=float(sig.get("target_pct", 0)),
                time_horizon=sig.get("time_horizon", horizon),
                summary=sig.get("summary", ""),
                thesis=sig.get("thesis", ""),
                risks=sig.get("risks", ""),
                debate_summary=sig.get("debate_summary", ""),
                qc_passed=bool(res.get("qc_passed")),
                qc_notes=(res.get("qc") or {}).get("notes", ""),
                raw={
                    "experts": res.get("experts"),
                    "debate": res.get("debate"),
                    "qc": res.get("qc"),
                    "brief_snapshot": res.get("brief_snapshot"),
                    "pm_output": sig,
                },
            )
            db.add(row)

        obj = await db.get(AnalysisRun, run_id)
        obj.status = "done"
        obj.finished_at = datetime.utcnow()

    # Emit Pine Script snapshot for this run
    try:
        await write_pine_script(run_id)
    except Exception:
        log.exception("Pine script write failed")

    return run_id


async def _current_portfolio_snapshot() -> dict[str, Any]:
    """Latest qc-passed BUY signals per ticker, newest first — a stand-in for a positions table until broker integration."""
    async with session_scope() as db:
        stmt = (
            select(Signal)
            .where(Signal.qc_passed == True, Signal.action == "BUY")
            .order_by(Signal.created_at.desc())
            .limit(50)
        )
        rows = (await db.execute(stmt)).scalars().all()
    seen = set()
    positions = []
    total = 0.0
    for r in rows:
        if r.ticker in seen:
            continue
        seen.add(r.ticker)
        positions.append({
            "ticker": r.ticker,
            "target_pct": r.target_pct,
            "entry_low": r.buy_low,
            "entry_high": r.buy_high,
            "stop_loss": r.stop_loss,
            "signal_at": r.created_at.isoformat(),
        })
        total += r.target_pct
    return {
        "positions": positions,
        "allocated_pct": total,
        "cash_pct": max(0.0, 100.0 - total),
    }
