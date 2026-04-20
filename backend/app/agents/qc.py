from __future__ import annotations

from typing import Any

import orjson

from app.agents.base import load_prompt
from app.agents.claude_client import get_claude


async def run_qc(
    signal: dict[str, Any],
    brief: dict[str, Any],
    risk_settings: dict[str, Any],
    portfolio_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claude = get_claude()
    system = load_prompt("qc")

    payload = {
        "proposed_signal": signal,
        "risk_settings": risk_settings,
        "technicals_summary": brief.get("indicators_daily"),
        "quote": brief.get("quote"),
        "portfolio_snapshot": portfolio_snapshot or {"positions": [], "cash_pct": 100.0},
    }
    user = (
        "Audit this proposed signal. Run all checks. Return the JSON contract.\n\n"
        f"```json\n{orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()}\n```"
    )

    try:
        result = await claude.json_complete(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=claude.parse_model,  # Haiku is sufficient for structured audit
            max_tokens=1500,
            temperature=0.1,
        )
    except Exception as e:
        result = {
            "passed": False,
            "action_taken": "reject",
            "issues": [f"QC error: {e}"],
            "warnings": [],
            "checks": {},
            "modifications": {},
            "notes": "QC failed to run — signal rejected by default.",
        }

    # Apply modifications if QC asked to
    modified = dict(signal)
    mods = result.get("modifications") or {}
    if result.get("action_taken") in ("modify", "accept") and isinstance(mods, dict):
        for k, v in mods.items():
            if k in modified and v is not None:
                modified[k] = v
    if result.get("action_taken") == "downgrade":
        modified["action"] = "HOLD"
        modified["target_pct"] = 0
    if result.get("action_taken") == "reject":
        modified["action"] = "HOLD"
        modified["target_pct"] = 0

    return {
        "passed": bool(result.get("passed")),
        "report": result,
        "signal": modified,
    }
