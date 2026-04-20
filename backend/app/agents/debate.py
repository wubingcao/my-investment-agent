"""Structured committee debate.

Flow:
  round 1: each expert analyzes independently (parallel)
  round 2..N: each expert sees peers' verdicts, must rebut one disagreement,
              may update their own view (parallel)
  output: list of all verdicts per round + final verdict per expert
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agents.experts import get_experts
from app.config import get_settings

log = logging.getLogger(__name__)


async def run_debate(brief: dict[str, Any], macro: dict[str, Any], horizon: str) -> dict[str, Any]:
    cfg = get_settings()
    experts = get_experts()

    # Round 1: independent analysis
    r1: list[dict[str, Any]] = await asyncio.gather(
        *(e.analyze(brief, macro, horizon) for e in experts),
        return_exceptions=False,
    )

    all_rounds: list[list[dict[str, Any]]] = [r1]
    transcript: list[dict[str, Any]] = []
    for idx, v in enumerate(r1):
        transcript.append({
            "round": 1,
            "expert": v["expert"],
            "stance": "opening",
            "argument": v["thesis"],
            "rebuttal_to": None,
        })

    current = r1
    for rnd in range(2, cfg.debate_rounds + 1):
        revised: list[dict[str, Any]] = await asyncio.gather(
            *(
                experts[i].rebut(
                    brief,
                    current[i],
                    [o for j, o in enumerate(current) if j != i],
                    horizon,
                )
                for i in range(len(experts))
            ),
        )
        all_rounds.append(revised)
        for r in revised:
            transcript.append({
                "round": rnd,
                "expert": r["expert"],
                "stance": "revision",
                "argument": r["thesis"],
                "rebuttal_to": None,
            })
        current = revised

    return {
        "rounds": all_rounds,
        "final_verdicts": current,
        "transcript": transcript,
    }


def consensus_signal(verdicts: list[dict[str, Any]], experts, horizon: str) -> dict[str, Any]:
    """Quick weighted vote used as a pre-check before Portfolio Manager."""
    buckets = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
    for v, ex in zip(verdicts, experts):
        w = ex.weight_for(horizon) * float(v.get("confidence", 0))
        buckets[v["action"]] += w
    action = max(buckets, key=buckets.get)
    total = sum(buckets.values()) or 1.0
    return {
        "action": action,
        "score": buckets[action] / total,
        "breakdown": buckets,
    }
