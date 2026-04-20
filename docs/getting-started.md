# Getting started

## 1. Prerequisites

- **Python 3.11+** — `python --version`
- **Node.js 20+** — `node --version`
- **Anthropic API key** — https://console.anthropic.com/

Optional (all free tiers):
- **Finnhub** — https://finnhub.io/ (company news + earnings calendar)
- **NewsAPI** — https://newsapi.org/ (broad market news)
- **FRED** — https://fred.stlouisfed.org/docs/api/api_key.html (macro data)

## 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env — paste your ANTHROPIC_API_KEY
python run.py
```

Backend will:
- create `investment_agent.db` (SQLite) on first run
- expose http://localhost:8000 with interactive docs at `/docs`
- start the APScheduler for daily/weekly/monthly jobs

## 3. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173.

## 4. First analysis

1. Add tickers (e.g. `AAPL`, `NVDA`, `TSLA`) to the watchlist
2. Choose horizon (default: Swing)
3. Click **Re-run latest watchlist** (or type ad-hoc tickers and click Analyze tickers)
4. Watch the committee debate. First run takes ~60–120s for 3 tickers (parallelism capped at 4).
5. Click a signal card to open the dashboard view with TradingView Lightweight Charts + debate transcript
6. Download the **Pine Script** to paste into TradingView's Pine Editor → Add to chart

## 5. Scheduled jobs

Defaults in `.env`:

| Job | Default cron | Purpose |
|-----|--------------|---------|
| Daily watchlist scan | `30 8 * * MON-FRI` | 08:30 weekday pre-market sweep |
| Daily performance eval | `0 17 * * MON-FRI` | 17:00 grade settled signals |
| Weekly learnings | `0 18 * * SUN` | Markdown lessons from outcomes |
| Monthly skills | `0 19 1 * *` | Distill learnings into reusable skills |

Adjust any of them in `.env` without code changes.

## 6. Where things land

- SQLite: `backend/investment_agent.db`
- Pine scripts: `pine_scripts/run_<id>.pine`
- Knowledge base: `knowledge_base/learnings/`, `knowledge_base/skills/`
- Cache: `backend/data_cache/` (safe to delete — will rebuild)
- Logs: stderr from uvicorn

## 7. Editing the agents

Each expert's system prompt is a markdown file at `backend/app/agents/prompts/*.md`.
You can edit these live — the next analysis run picks up changes (no restart needed
for prompt-only edits).

## 8. Troubleshooting

**"RuntimeError: ANTHROPIC_API_KEY missing"** — populate `.env` in `backend/`.

**"No price data — ticker may be invalid or delisted"** — yfinance couldn't find that ticker. Check the symbol (use `.TO` for Canadian, `.HK` for Hong Kong, etc.).

**Daily scans not firing** — your PC must be on at the scheduled time. For always-on scheduling consider a cheap VPS or GitHub Actions (Phase 3).

**Pine script doesn't draw lines on TV** — make sure the ticker you're viewing in TV matches the `syminfo.ticker` (e.g. NYSE:AAPL vs AAPL). The script checks `syminfo.ticker` which is the plain symbol.

**Weekly learnings empty** — need several scored outcomes first. After ~2 weeks of daily scans, the performance evaluator will have graded enough signals.
