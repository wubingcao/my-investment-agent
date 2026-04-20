from __future__ import annotations

from typing import Any

import orjson

from app.agents.base import load_prompt
from app.agents.claude_client import get_claude


async def synthesize(
    brief: dict[str, Any],
    macro: dict[str, Any],
    debate_result: dict[str, Any],
    horizon: str,
    risk_settings: dict[str, Any],
    portfolio_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claude = get_claude()
    system = load_prompt("portfolio_manager")

    payload = {
        "ticker": brief["ticker"],
        "horizon": horizon,
        "risk_settings": risk_settings,
        "portfolio_snapshot": portfolio_snapshot or {"positions": [], "cash_pct": 100.0},
        "technicals": brief.get("indicators_daily"),
        "intraday_technicals": brief.get("indicators_intraday"),
        "quote": brief.get("quote"),
        "fundamentals": brief.get("fundamentals"),
        "macro": macro,
        "expert_final_verdicts": debate_result["final_verdicts"],
        "debate_rounds": len(debate_result["rounds"]),
    }
    user = (
        "Synthesize the committee output into a final signal.\n\n"
        f"```json\n{orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()}\n```\n\n"
        "Apply your decision rules and return the JSON contract."
    )

    try:
        result = await claude.json_complete(
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=2500,
            temperature=0.35,
        )
    except Exception as e:
        result = {
            "ticker": brief["ticker"],
            "action": "HOLD",
            "confidence": 0.0,
            "target_pct": 0,
            "time_horizon": horizon,
            "thesis": f"PM synthesis failed: {e}",
            "risks": "",
            "debate_summary": "",
            "reasoning_steps": [],
        }

    # Sanity clamps
    result.setdefault("ticker", brief["ticker"])
    result.setdefault("time_horizon", horizon)
    result.setdefault("summary", "")
    result.setdefault("thesis", "")
    result.setdefault("risks", "")
    result.setdefault("debate_summary", "")
    result["target_pct"] = _clamp_pct(result.get("target_pct", 0), risk_settings.get("max_position_pct", 15))
    try:
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0))))
    except Exception:
        result["confidence"] = 0.0
    if result.get("action") not in {"BUY", "SELL", "HOLD"}:
        result["action"] = "HOLD"
    if result["action"] == "HOLD":
        result["target_pct"] = 0

    # Always have SOMETHING in summary
    if not result["summary"]:
        first_sentence = (result["thesis"] or "").split(". ")[0]
        result["summary"] = (first_sentence[:220] + "…") if len(first_sentence) > 220 else first_sentence
    return result


def _clamp_pct(val: Any, max_pct: float) -> float:
    try:
        v = float(val)
    except Exception:
        v = 0.0
    return max(0.0, min(float(max_pct), v))
