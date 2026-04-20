"""Per-ticker orchestration: data → experts → debate → PM synthesis → QC → signal."""
from __future__ import annotations

import logging
from typing import Any

from app.agents import debate as debate_mod
from app.agents import portfolio_manager, qc
from app.agents.experts import get_experts
from app.data import aggregator

log = logging.getLogger(__name__)


async def analyze_ticker(
    ticker: str,
    horizon: str,
    risk_settings: dict[str, Any],
    macro: dict[str, Any] | None = None,
    portfolio_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = ticker.upper().strip()
    log.info("Analyzing %s (horizon=%s)", ticker, horizon)

    brief = await aggregator.build_research_brief(ticker)
    if not brief["quote"].get("price"):
        return _empty_error(ticker, horizon, "No price data — ticker may be invalid or delisted.")

    if macro is None:
        macro_ctx = await aggregator.build_macro_context()
        macro = macro_ctx["macro"]

    debate_res = await debate_mod.run_debate(brief, macro, horizon)

    pm_signal = await portfolio_manager.synthesize(
        brief=brief,
        macro=macro,
        debate_result=debate_res,
        horizon=horizon,
        risk_settings=risk_settings,
        portfolio_snapshot=portfolio_snapshot,
    )

    qc_res = await qc.run_qc(
        signal=pm_signal,
        brief=brief,
        risk_settings=risk_settings,
        portfolio_snapshot=portfolio_snapshot,
    )
    final_signal = qc_res["signal"]

    return {
        "ticker": ticker,
        "horizon": horizon,
        "signal": final_signal,
        "qc": qc_res["report"],
        "qc_passed": qc_res["passed"],
        "experts": debate_res["final_verdicts"],
        "debate": debate_res["transcript"],
        "brief_snapshot": {
            "quote": brief["quote"],
            "indicators_daily": brief["indicators_daily"],
            "indicators_intraday": brief["indicators_intraday"],
        },
    }


def _empty_error(ticker: str, horizon: str, msg: str) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "horizon": horizon,
        "signal": {
            "ticker": ticker, "action": "HOLD", "confidence": 0.0,
            "target_pct": 0, "time_horizon": horizon,
            "thesis": msg, "risks": "", "debate_summary": "",
        },
        "qc": {"passed": False, "issues": [msg], "warnings": [], "checks": {}},
        "qc_passed": False,
        "experts": [],
        "debate": [],
        "brief_snapshot": {},
    }
