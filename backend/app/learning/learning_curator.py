"""Weekly learning job.

Reads recent scored outcomes, separates wins from losses by expert consensus,
asks Claude to produce a markdown "lessons learned" doc, and writes it to
knowledge_base/learnings/YYYY-MM-DD.md. The resulting doc becomes RAG context
for future analyses.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, join, and_

from app.agents.claude_client import get_claude
from app.config import get_settings
from app.db import session_scope
from app.models import Signal, SignalOutcome

log = logging.getLogger(__name__)


LEARNING_SYSTEM = """You are the Learning Curator for a multi-agent investment system.
Your job: look at the past week of signals the committee produced, whether they were
right or wrong, and distill actionable lessons. Be specific, not generic.

Output a MARKDOWN document with:
1. # Week in review — dates, win rate, avg pnl
2. ## What worked — bullet lessons, each tied to a concrete trade
3. ## What failed — bullet lessons, each tied to a concrete trade
4. ## Patterns across experts — who was systematically right/wrong and when
5. ## Recommended adjustments — concrete prompt tweaks or weighting changes
Keep it tight. Prefer specific "when X pattern appeared, Y outcome" lessons.
"""


async def run_weekly_learnings(days_back: int = 14) -> str:
    cfg = get_settings()
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    async with session_scope() as db:
        stmt = (
            select(Signal, SignalOutcome)
            .join(SignalOutcome, SignalOutcome.signal_id == Signal.id)
            .where(Signal.created_at >= cutoff)
            .limit(80)
        )
        rows = (await db.execute(stmt)).all()

    if not rows:
        log.info("Weekly learnings skipped: no scored outcomes yet")
        return ""

    cases = []
    for sig, out in rows:
        cases.append({
            "ticker": sig.ticker,
            "action": sig.action,
            "confidence": sig.confidence,
            "horizon": sig.time_horizon,
            "thesis": sig.thesis[:300],
            "risks": sig.risks[:200],
            "pnl_pct": out.pnl_pct,
            "hit_target": out.hit_target,
            "hit_stop": out.hit_stop,
            "expert_verdicts": [
                {"expert": e.get("expert"), "action": e.get("action"), "conf": e.get("confidence")}
                for e in (sig.raw or {}).get("experts", [])
            ],
            "created_at": sig.created_at.isoformat(),
        })

    win = sum(1 for c in cases if (c["pnl_pct"] or 0) > 0)
    win_rate = win / len(cases) if cases else 0
    avg_pnl = sum(c["pnl_pct"] or 0 for c in cases) / len(cases) if cases else 0

    import orjson
    user_msg = (
        f"Past {days_back} days — {len(cases)} scored signals. Win rate {win_rate:.0%}. Avg PnL {avg_pnl:.2f}%.\n\n"
        f"Case data:\n```json\n{orjson.dumps(cases[:40], option=orjson.OPT_INDENT_2).decode()}\n```\n\n"
        "Produce the lessons-learned markdown document now."
    )

    claude = get_claude()
    md = await claude.complete(
        system=LEARNING_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=3500,
        temperature=0.4,
    )

    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = cfg.kb_path / "learnings"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.md"
    path.write_text(md, encoding="utf-8")
    log.info("Weekly learnings written to %s", path)

    # Refresh index
    await _refresh_index(cfg.kb_path / "learnings", "# Learnings index")
    return str(path)


async def _refresh_index(dir_path, header: str):
    dir_path.mkdir(parents=True, exist_ok=True)
    entries = sorted(dir_path.glob("*.md"), reverse=True)
    lines = [header, ""]
    for e in entries:
        if e.name == "README.md":
            continue
        lines.append(f"- [{e.stem}]({e.name})")
    (dir_path / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
