# Agent committee reference

## Why multiple experts?

Markets are reflexive — no single lens captures everything. A Buffett-style
filter alone would have missed every growth rotation of the last decade; a
pure technical filter would have bought every blow-off top. The committee
design forces each ticker through four independent lenses and lets a debate
surface what any single lens misses.

## The four personas

| Persona | Home turf | Prompt file | Edge |
|---------|-----------|-------------|------|
| **Buffett / Munger** | Fundamentals, moats | `buffett_munger.md` | Rejects stories, anchors to cash flow, rare high-conviction calls |
| **Dalio / Druckenmiller** | Macro regime, liquidity | `dalio_druckenmiller.md` | Frames trades against rates/dollar/VIX backdrop |
| **Paul Tudor Jones / Schwartz** | Price action, swing | `ptj_schwartz.md` | Required entry/exit/stop numbers; 3:1 R:R rule |
| **Burry / Chanos** | Contrarian, short bias | `burry_chanos.md` | Adversarial pressure — surfaces red flags others gloss over |

Each persona is a single Claude call with a dedicated system prompt. Add new
personas by dropping a markdown file into `backend/app/agents/prompts/` and
registering it in `backend/app/agents/experts/__init__.py`.

## The debate protocol

1. **Round 1 — independent analysis.** All four experts analyze the ticker in
   parallel. Their output is a structured JSON verdict.
2. **Round 2 — rebuttal.** Each expert sees peers' verdicts and must (a) rebut
   the strongest opposing view, (b) revise or reaffirm their own.
3. **Optional further rounds** — configured via `DEBATE_ROUNDS` (default 2).
4. **No forced consensus** — dissent is preserved and surfaced to the
   Portfolio Manager, which uses it to discount confidence.

## Portfolio Manager

The PM is a separate Claude call (prompt: `portfolio_manager.md`). It receives
the final-round verdicts + debate transcript + technicals + risk settings and
produces the final signal:
- action (BUY/SELL/HOLD) with confidence
- entry range, exit range, stop loss
- target % of portfolio (volatility-scaled)
- thesis, risks, debate summary

Expert weights bias by horizon (PTJ ×1.5 for day, Buffett ×1.4 for position)
but the PM can override by reading the prompt.

## QC agent (veto power)

The QC runs on Haiku for cost efficiency. It checks:
- **Data freshness** — is the quote/technicals within last session?
- **Internal consistency** — price bands match action, stop on correct side
- **Risk sanity** — R:R ≥ 2:1, stop 1–10% depending on horizon
- **Thesis–action coherence** — does the thesis actually support the action?
- **Concentration** — does this crowd existing exposure?

QC actions: `accept`, `modify` (tweak values), `downgrade` (force HOLD),
`reject`. Modifications are applied to the final signal before it's persisted.

## Self-improvement loop

| Cadence | Job | What it produces |
|---------|-----|------------------|
| Daily (weekday 17:00) | `performance_evaluator` | SignalOutcome rows — pnl, hit target/stop |
| Weekly (Sun 18:00) | `learning_curator` | `knowledge_base/learnings/YYYY-MM-DD.md` |
| Monthly (1st 19:00) | `skill_synthesizer` | `knowledge_base/skills/*.md` playbooks |

The learning curator prompt is inline in `learning_curator.py` and the skill
synthesizer prompt in `skill_synthesizer.py` — both editable.

## Extending

- **New expert** — drop prompt in `prompts/`, register in `experts/__init__.py`
  with horizon weights, restart backend.
- **New data source** — add module under `data/`, expose from `aggregator.py`.
- **New scheduled job** — add a coroutine in `scheduler/jobs.py`, register with APScheduler.
- **Different model** — swap `CLAUDE_DEBATE_MODEL` / `CLAUDE_PARSE_MODEL` in `.env`.
- **Multi-model debate** — subclass `BaseExpert` to route specific personas to
  GPT or Gemini; swap the `claude_client` dependency.
