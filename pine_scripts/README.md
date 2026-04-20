# Pine Scripts

Auto-generated TradingView Pine v5 indicators, one per analysis run.

## How to use

1. Run an analysis in the dashboard (or wait for the scheduled daily scan).
2. From the Dashboard signal card **or** History → run detail, click **Download .pine**.
3. In TradingView, open the Pine Editor (bottom panel) → paste → **Add to chart**.
4. The indicator will:
   - Shade the chart background green/red/gray based on the signal
   - Draw horizontal lines for entry band, exit band, and stop loss
   - Place a labelled marker (`BUY conf=0.72 size=8.5%`) on the last bar

The script targets the symbol you're viewing in TradingView (`syminfo.ticker`) —
only fires its overlay if that symbol is in the generated run.

## Compatibility

Works on every TradingView plan tier **including Essential** — it does not
rely on webhook alerts. For users on Pro+/Premium you can extend these
scripts to fire alerts; see `docs/architecture.md`.
