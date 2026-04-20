from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agents.claude_client import get_claude

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


@dataclass
class ExpertConfig:
    name: str          # stable id, e.g. "buffett_munger"
    display: str       # pretty name, e.g. "Buffett / Munger"
    prompt_file: str   # markdown prompt filename (without .md)
    weight_day: float = 1.0
    weight_swing: float = 1.0
    weight_position: float = 1.0


class BaseExpert:
    def __init__(self, config: ExpertConfig):
        self.config = config
        self._system = load_prompt(config.prompt_file)
        self._claude_cached = None

    @property
    def _claude(self):
        # Lazy-init so a missing API key doesn't crash module import.
        if self._claude_cached is None:
            self._claude_cached = get_claude()
        return self._claude_cached

    def weight_for(self, horizon: str) -> float:
        return {
            "day": self.config.weight_day,
            "swing": self.config.weight_swing,
            "position": self.config.weight_position,
        }.get(horizon, 1.0)

    async def analyze(self, brief: dict[str, Any], macro: dict[str, Any], horizon: str) -> dict[str, Any]:
        user = self._build_user_message(brief, macro, horizon)
        try:
            verdict = await self._claude.json_complete(
                system=self._system,
                messages=[{"role": "user", "content": user}],
                max_tokens=2000,
                temperature=0.55,
            )
        except Exception as e:
            return {
                "expert": self.config.display,
                "action": "HOLD",
                "confidence": 0.0,
                "thesis": f"Error during analysis: {e}",
                "key_points": [],
                "risks": [],
                "price_target": None,
                "entry_range": None,
                "exit_range": None,
            }
        verdict = self._normalize(verdict)
        verdict["expert"] = self.config.display
        return verdict

    async def rebut(self, brief: dict[str, Any], own_verdict: dict[str, Any], others: list[dict[str, Any]], horizon: str) -> dict[str, Any]:
        others_summary = "\n\n".join(
            f"**{o['expert']}** ({o['action']}, conf {o.get('confidence', 0):.2f}): {o.get('thesis', '')}"
            for o in others
        )
        user = (
            f"Ticker: {brief['ticker']}  |  Horizon: {horizon}\n\n"
            f"Your initial verdict:\n{own_verdict.get('action')} conf {own_verdict.get('confidence')}\n"
            f"Thesis: {own_verdict.get('thesis')}\n\n"
            f"Other committee members said:\n{others_summary}\n\n"
            "Respond as this expert:\n"
            "1. Which other expert makes the strongest point you disagree with? Rebut it briefly.\n"
            "2. Is there any evidence that would make you update YOUR verdict?\n"
            "3. Return a revised JSON verdict using the SAME schema. If nothing changed, return the same values with a brief note in thesis about why you're holding position.\n"
        )
        try:
            revised = await self._claude.json_complete(
                system=self._system,
                messages=[{"role": "user", "content": user}],
                max_tokens=1500,
                temperature=0.55,
            )
        except Exception:
            revised = own_verdict
        revised = self._normalize(revised)
        revised["expert"] = self.config.display
        return revised

    def _build_user_message(self, brief: dict[str, Any], macro: dict[str, Any], horizon: str) -> str:
        import orjson
        # Trim brief to keep token costs sane
        compact = self._compact_brief(brief)
        return (
            f"Analyze {brief['ticker']} for a {horizon}-horizon trade.\n\n"
            f"# Research brief\n```json\n{orjson.dumps(compact, option=orjson.OPT_INDENT_2).decode()}\n```\n\n"
            f"# Macro context\n```json\n{orjson.dumps(macro, option=orjson.OPT_INDENT_2).decode()}\n```\n\n"
            f"Produce your JSON verdict now."
        )

    @staticmethod
    def _compact_brief(brief: dict[str, Any]) -> dict[str, Any]:
        return {
            "ticker": brief.get("ticker"),
            "quote": brief.get("quote"),
            "fundamentals": brief.get("fundamentals"),
            "indicators_daily": brief.get("indicators_daily"),
            "indicators_intraday": brief.get("indicators_intraday"),
            "recent_bars_tail": (brief.get("recent_bars_daily") or [])[-15:],
            "company_news_top5": (brief.get("company_news") or [])[:5],
            "market_news_top5": (brief.get("market_news") or [])[:5],
            "earnings_next": (brief.get("earnings_calendar") or [])[:1],
        }

    @staticmethod
    def _normalize(v: dict[str, Any]) -> dict[str, Any]:
        action = str(v.get("action", "HOLD")).upper()
        if action not in {"BUY", "SELL", "HOLD"}:
            action = "HOLD"
        try:
            conf = float(v.get("confidence", 0))
        except Exception:
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        return {
            "action": action,
            "confidence": conf,
            "thesis": v.get("thesis", ""),
            "key_points": v.get("key_points", []) or [],
            "risks": v.get("risks", []) or [],
            "price_target": v.get("price_target"),
            "entry_range": v.get("entry_range"),
            "exit_range": v.get("exit_range"),
        }
