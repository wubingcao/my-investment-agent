# Architecture

## Components

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         React SPA (Vite, port 5173)                        │
│     Dashboard · Watchlist · Debate transcript · Lightweight Charts        │
│     History · Settings · Pine script download                              │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ /api/*
┌──────────────────────────────────▼────────────────────────────────────────┐
│                    FastAPI backend (uvicorn, port 8000)                    │
│                                                                            │
│  api/        ┌─analyze, signals, history, watchlist, settings             │
│  services/   ┌─analysis_service (orchestrate run persistence)             │
│              └─pine_script_service, settings_service                      │
│  agents/     ┌─claude_client (prompt cache + retries)                     │
│              ├─base, experts/ (4 personas)                                │
│              ├─debate (multi-round parallel rebuttals)                    │
│              ├─portfolio_manager (final synthesis)                        │
│              ├─qc (validation, risk checks)                               │
│              ├─orchestrator (per-ticker pipeline)                         │
│              └─prompts/ (markdown system prompts, editable hot)           │
│  data/       ┌─yahoo, finnhub, newsapi, fred, technical, cache, aggregator│
│  scheduler/  └─APScheduler — daily scan, perf-eval, weekly, monthly       │
│  learning/   ┌─performance_evaluator (outcomes vs signals)                │
│              ├─learning_curator (weekly md lessons → knowledge_base/)     │
│              └─skill_synthesizer (monthly skills markdown)                │
│  models, db  └─SQLAlchemy 2.0 async on SQLite                             │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │
               ┌───────────────────┼──────────────────────────┐
               ▼                   ▼                          ▼
     ┌──────────────────┐ ┌───────────────┐  ┌────────────────────────┐
     │ investment_agent │ │ knowledge_base │  │    pine_scripts/       │
     │   .db (SQLite)   │ │  (markdown)    │  │  run_<id>.pine         │
     │                  │ │                │  │                        │
     │ watchlist        │ │ learnings/     │  │ TradingView indicator  │
     │ analysis_run     │ │ skills/        │  │ (Essential-plan ready) │
     │ signal           │ │ fundamentals/  │  └────────────────────────┘
     │ signal_outcome   │ │ technicals/    │
     │ setting          │ └───────────────┘
     └──────────────────┘
```

## Per-ticker analysis pipeline

```
          ┌───────────────────────────┐
          │  aggregator.build_brief   │  quote + fundamentals + indicators
          │    + build_macro_context  │  + news + earnings + macro regime
          └─────────────┬─────────────┘
                        ▼
           ┌─────────────────────────┐
           │  debate.run_debate      │
           │  round 1: 4 × analyze() │  (parallel, Claude Opus)
           │  round 2: 4 × rebut()   │  (each sees peers' verdicts)
           └─────────────┬───────────┘
                         ▼
            ┌───────────────────────┐
            │ portfolio_manager     │  synth → action, price bands, size
            │     .synthesize()     │
            └───────────┬───────────┘
                        ▼
               ┌──────────────────┐
               │   qc.run_qc()    │  validates or downgrades/modifies
               │ (Claude Haiku)   │  — veto authority
               └─────────┬────────┘
                         ▼
               ┌──────────────────┐
               │  persist Signal  │  + write pine script + expose via API
               └──────────────────┘
```

## Self-improvement loop

- **daily 17:00 weekdays** — `performance_evaluator` grades signals old enough to have a resolved outcome (walk-forward the bars, check target/stop hits, compute pnl).
- **Sunday 18:00** — `learning_curator` reads last 14 days of outcomes and asks Claude to produce a markdown lessons-learned doc in `knowledge_base/learnings/YYYY-MM-DD.md`. Updates index.
- **1st of month 19:00** — `skill_synthesizer` reads recent learnings and distills recurring patterns into `knowledge_base/skills/*.md` — reusable playbooks future expert prompts can read.
- **capability improvement** — because expert prompts live as markdown in `backend/app/agents/prompts/`, you (or later, an automated job) can edit them based on learnings. This is the deliberate tight loop: outcomes → learnings → skills → prompt refinement.

## Design notes

- **Why Claude only (for now):** single vendor, two-tier model strategy (Opus for reasoning, Haiku for parsing/QC) keeps cost predictable and avoids cross-vendor schema drift. Debate diversity comes from persona prompts, not different models.
- **Why markdown everything:** prompts, learnings, and skills are all markdown so they can be edited, diffed in git, and grafted into future prompts as RAG context without schema churn.
- **Why free data tier:** yfinance + Finnhub free + NewsAPI free + FRED is sufficient for day/swing decisions; upgrade later by swapping one module at a time.
- **Why Pine Script (not webhooks):** TradingView Essential doesn't support webhook alerts; a static Pine indicator works on every plan tier.
- **Why SQLite:** single file, easy backup, fine for single-user local. Swap to Postgres by changing DATABASE_URL.
