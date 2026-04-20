# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the system

**Backend** (FastAPI + uvicorn, port 8000):
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then fill in ANTHROPIC_API_KEY
python run.py
```
API docs live at http://localhost:8000/docs. Auto-reload is disabled by default because it is unreliable on Windows paths with spaces — opt in with `RELOAD=1 python run.py`.

**Frontend** (Vite + React, port 5173):
```bash
cd frontend
npm install
npm run dev
```
On Windows, Vite binds IPv6-only, so use `http://localhost:5173` (not `127.0.0.1`).

**Trigger a single analysis via curl:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"], "time_horizon": "swing"}'
```

**Type-check the frontend:**
```bash
cd frontend && npx tsc --noEmit
```

## Architecture

### Per-ticker pipeline

Every `POST /api/analyze` call runs through `analysis_service.run_analysis`, which is the entry point for everything:

```
aggregator.build_research_brief(ticker)          # parallel: yfinance + Finnhub + NewsAPI + FRED + technicals
  └─> debate.run_debate(brief, macro, horizon)   # 2 rounds, 4 experts in parallel (Claude Opus)
        └─> portfolio_manager.synthesize(...)    # committee verdict → BUY/SELL/HOLD + price bands (Claude Opus)
              └─> qc.run_qc(signal, ...)         # validation + optional downgrade (Claude Haiku, temp=0.1)
                    └─> Signal row persisted + Pine Script written
```

All four stages are in `backend/app/agents/`. Each expert is a prompt file in `backend/app/agents/prompts/` (Markdown). Changing a prompt is enough to change expert behavior — no code changes needed.

### Debate mechanics

`debate.py` runs `expert.analyze(brief)` for all four experts in parallel (round 1), then for rounds 2+ calls `expert.rebut(brief, peer_verdicts)` again in parallel. Each expert returns a `ExpertVerdict` dict. The full debate transcript is stored in `Signal.raw["debate"]`.

### QC authority

The QC agent in `qc.py` has veto power: it can accept, modify fields (confidence, target_pct), downgrade the action to HOLD, or reject the signal entirely. It uses Claude Haiku at near-zero temperature for deterministic output.

### Data layer

- **SQLite** with async SQLAlchemy 2.0 (`backend/app/db.py`). Schema auto-migrates on startup via `_auto_migrate()` — it checks `PRAGMA table_info` and issues `ALTER TABLE` for any missing columns. Add new migrations there.
- **Models** (`backend/app/models.py`): `AnalysisRun`, `Signal` (has `.raw` JSON blob for full debate/QC data), `SignalOutcome`, `Watchlist`, `Setting`.
- **API response shape** is in `backend/app/api/signals.py::_signal_out()`. When adding a new model field, update `_signal_out`, `Signal` model, `analysis_service`, and `_auto_migrate` together.

### Frontend

The Vite proxy (`/api/*` → `http://localhost:8000`) means all API calls in `frontend/src/api/client.ts` just use `/api/...` with no CORS concerns. Key layout:
- `Dashboard.tsx` owns most state: watchlist selection, tile grid, modal open state.
- `SignalTile.tsx` is the per-ticker card; clicking it opens the detail view, clicking ⓘ opens `SignalSummaryModal.tsx`.
- `SignalSummaryModal.tsx` fetches `signalsApi.detail(id)` on open (includes experts + debate arrays that aren't in the list endpoint).

### Scheduler

APScheduler in `backend/app/scheduler/jobs.py` runs three background jobs (cron-based, config-driven):
- **Daily** (default 08:30 weekdays): full watchlist scan
- **Weekly** (Sunday 18:00): learning curator reads signal outcomes, writes Markdown lessons to `knowledge_base/learnings/`
- **Monthly** (1st of month 19:00): skill synthesizer distills learnings into `knowledge_base/skills/`

The learning/skill jobs are Phase 2 stubs — they log but don't yet produce real output.

## Key quirks

**Temperature deprecated on Opus 4.5+** — `claude_client._model_rejects_temperature()` detects model name and omits the `temperature` kwarg. If adding new model strings, keep this updated.

**Empty API key injection** — The Claude Code harness injects `ANTHROPIC_API_KEY=""` into subprocesses. `config.py` detects and drops empty-string values before calling `load_dotenv()`, letting the real `.env` value win.

**Claude JSON extraction** — `ClaudeClient.extract_json()` strips markdown fences then falls back to regex `{...}` search. Never call `.json()` on raw model output directly.

**Prompt caching** — System prompts are sent with `cache_control: {"type": "ephemeral"}` which gives a 5-minute server-side cache. Repeated analyses on the same ticker within that window see cache hits.

**`Signal.raw` is the ground truth** — The database columns hold the distilled signal. The full expert verdicts, complete debate transcript, QC report, and brief snapshot are all in `Signal.raw` (JSON). The `/signals/{id}` endpoint unpacks them when `include_raw=True`.

**Pine Script** — `pine_script_service.write_pine_script(run_id)` writes one `.pine` file per run to `pine_scripts/`. The file encodes all signals for that run as Pine arrays so it works on TradingView Essential (no webhooks).
