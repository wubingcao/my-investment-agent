# My Investment Agent

A multi-agent stock portfolio system that produces buy/sell signals, price bands, and position sizing through a committee of hedge-fund expert personas, structured debate, and QC validation. Built on Claude (Opus 4.7 + Haiku 4.5) with a self-improvement loop that turns trading outcomes into markdown learnings, skills, and a growing knowledge base.

## Architecture

```
                             ┌───────────────────────────────┐
                             │       Data Layer (cached)     │
                             │  yfinance / Finnhub /         │
                             │  NewsAPI / FRED / indicators  │
                             └──────────────┬────────────────┘
                                            │
                   ┌────────────────────────┴────────────────────────┐
                   │                 Orchestrator                    │
                   │  (LangGraph-style state machine, per ticker)    │
                   └────────────────────────┬────────────────────────┘
                                            │  parallel
      ┌──────────────┬─────────────┬────────┴─────────┬───────────────┐
      │ Buffett /    │ Dalio /     │ PTJ /            │ Burry /       │
      │ Munger       │ Druckenmil. │ Schwartz         │ Chanos        │
      │ (value)      │ (macro)     │ (technical)      │ (contrarian)  │
      └──────┬───────┴──────┬──────┴────────┬─────────┴───────┬───────┘
             │              │               │                 │
             └──────────────┴───────┬───────┴─────────────────┘
                                    ▼
                          ┌──────────────────┐
                          │   Debate Layer   │   2 rounds + rebuttal
                          │  (rebut + refine)│   dissent flagged
                          └─────────┬────────┘
                                    ▼
                          ┌──────────────────┐
                          │ Portfolio Mgr    │   synthesize → buy/sell,
                          │ (synthesis)      │   price band, % sizing
                          └─────────┬────────┘
                                    ▼
                          ┌──────────────────┐
                          │   QC Agent       │   validates data, risk,
                          │  (gatekeeper)    │   consistency, freshness
                          └─────────┬────────┘
                                    ▼
                ┌───────────────────┴─────────────────────┐
                │        Outputs                          │
                │  • SQLite: decisions, positions, evals  │
                │  • Dashboard: signals + debate + chart  │
                │  • TradingView Lightweight Charts       │
                │  • Pine Script signal indicator         │
                └─────────────────────────────────────────┘

        ┌──────────────────────────────────────────┐
        │   Self-Improvement Loop (scheduled)      │
        │   daily:   performance evaluator         │
        │   weekly:  learning curator → .md        │
        │   monthly: skill synthesizer + KB build  │
        └──────────────────────────────────────────┘
```

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+
- A Claude API key ([console.anthropic.com](https://console.anthropic.com/))
- (Optional) Finnhub, NewsAPI, FRED keys — all have free tiers

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env    # fill in ANTHROPIC_API_KEY and optional keys
python run.py
```

Backend runs at http://localhost:8000. Docs at http://localhost:8000/docs.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Dashboard at http://localhost:5173.

### First analysis
1. Open dashboard → Watchlist → add tickers (e.g. AAPL, NVDA, TSLA)
2. Click **Analyze** → agents run debate → signals appear with buy/sell/hold, price bands, sizing
3. Inspect **Debate Transcript** to see each expert's argument + rebuttals
4. Export **Pine Script** to paste into TradingView for signal overlays

## Project layout

```
backend/
  app/
    agents/         # expert personas, debate, portfolio manager, QC
    api/            # FastAPI endpoints
    data/           # market data, news, macro, technical indicators
    services/       # orchestration + persistence
    scheduler/      # APScheduler jobs (daily scan, weekly learning)
    learning/       # phase 2: performance evaluation & skill synthesis
frontend/
  src/              # React + Vite + Lightweight Charts
knowledge_base/
  learnings/        # markdown lessons from trade outcomes
  skills/           # reusable strategy patterns distilled from learnings
pine_scripts/       # generated TradingView indicator code
docs/               # design docs
```

## Roadmap

**Phase 1 (MVP — this build):** full pipeline end-to-end, dashboard, TV charts, Pine Script, daily scheduler.

**Phase 2 (next):** performance evaluator, weekly learning curator, monthly skill synthesizer, knowledge-base RAG.

**Phase 3 (future):** broker integration (Alpaca paper → live), multi-model debate diversity, options strategies.

## Disclaimer

Research and educational tool. Not investment advice. Past performance does not guarantee future results. Always validate signals before trading.
