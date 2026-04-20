import { useEffect, useMemo, useState } from "react";
import WatchlistPanel from "../components/WatchlistPanel";
import SignalCard from "../components/SignalCard";
import SignalTile from "../components/SignalTile";
import SignalSummaryModal from "../components/SignalSummaryModal";
import DebateTranscript from "../components/DebateTranscript";
import TradingViewChart from "../components/TradingViewChart";
import { analyzeApi, historyApi, signalsApi, watchlistApi } from "../api/client";
import type { ChartResponse, Horizon, Signal } from "../types";

export default function Dashboard() {
  const [selected, setSelected] = useState<string | null>(null);
  const [latest, setLatest] = useState<Signal[]>([]);
  const [horizon, setHorizon] = useState<Horizon>("swing");
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string>("");
  const [detail, setDetail] = useState<Signal | null>(null);
  const [chart, setChart] = useState<ChartResponse | null>(null);
  const [tickerInput, setTickerInput] = useState("");
  const [summaryOpenId, setSummaryOpenId] = useState<number | null>(null);

  async function refreshLatest() {
    const s = await signalsApi.latest(60);
    setLatest(s);
  }
  useEffect(() => { refreshLatest(); }, []);

  const perTicker = useMemo(() => {
    const m = new Map<string, Signal>();
    for (const s of latest) {
      if (!m.has(s.ticker)) m.set(s.ticker, s);
    }
    return m;
  }, [latest]);

  useEffect(() => {
    if (!selected) { setDetail(null); setChart(null); return; }
    const s = perTicker.get(selected);
    if (!s) { setDetail(null); setChart(null); return; }
    signalsApi.detail(s.id).then(setDetail);
    signalsApi.chart(s.id, "6mo", "1d").then(setChart);
  }, [selected, perTicker]);

  async function runAnalyze(tickers: string[]) {
    if (!tickers.length) return;
    setRunning(true); setRunMsg("Running committee debate…");
    try {
      const r = await analyzeApi.run(tickers, horizon);
      setRunMsg(`Run #${r.run_id} complete`);
      await refreshLatest();
    } catch (e: any) {
      setRunMsg(`Error: ${e?.message || "failed"}`);
    } finally { setRunning(false); }
  }

  function runFromInput() {
    const ts = tickerInput.split(/[,\s]+/).map(t => t.trim().toUpperCase()).filter(Boolean);
    if (ts.length) runAnalyze(ts);
    setTickerInput("");
  }

  async function runSelected() {
    if (selected) runAnalyze([selected]);
  }

  async function runAllWatchlist() {
    const wl = await watchlistApi.list();
    const tickers = wl.map(w => w.ticker);
    if (tickers.length) runAnalyze(tickers);
  }

  return (
    <div className="main">
      <aside className="sidebar">
        <WatchlistPanel selected={selected} onSelect={setSelected} onChange={refreshLatest} />

        <div className="panel">
          <h2>Run analysis</h2>
          <div className="col" style={{ gap: 8 }}>
            <select value={horizon} onChange={e => setHorizon(e.target.value as Horizon)}>
              <option value="day">Day (1–3d)</option>
              <option value="swing">Swing (2–15d)</option>
              <option value="position">Position (weeks–months)</option>
            </select>
            <input
              placeholder="ad-hoc tickers (AAPL, NVDA)"
              value={tickerInput}
              onChange={e => setTickerInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && runFromInput()}
            />
            <button onClick={runFromInput} disabled={running}>
              Analyze tickers
            </button>
            <button className="secondary" onClick={runSelected} disabled={running || !selected}>
              Analyze selected
            </button>
            <button className="secondary" onClick={runAllWatchlist} disabled={running}>
              Analyze full watchlist
            </button>
            {runMsg && <div className="small">{runMsg}</div>}
          </div>
        </div>
      </aside>

      <main className="content">
        {!selected && (
          <>
            <div className="panel">
              <h2>Latest signals</h2>
              {latest.length === 0 ? (
                <div className="small">No signals yet. Add tickers and run an analysis.</div>
              ) : (
                <div className="tile-grid">
                  {Array.from(perTicker.values()).map(s => (
                    <SignalTile
                      key={s.id}
                      signal={s}
                      onOpenDetail={() => setSelected(s.ticker)}
                      onOpenSummary={() => setSummaryOpenId(s.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {selected && detail && (
          <>
            <SignalCard signal={detail} />
            {chart && (
              <div className="panel">
                <div className="row space" style={{ alignItems: "center" }}>
                  <h2 style={{ margin: 0 }}>{detail.ticker} — daily chart</h2>
                  <span className="small">
                    RSI14 {chart.indicators?.rsi14?.toFixed?.(1) ?? "—"} · trend {chart.indicators?.trend ?? "—"} · ATR{" "}
                    {chart.indicators?.atr14?.toFixed?.(2) ?? "—"}
                  </span>
                </div>
                <div style={{ marginTop: 8 }}>
                  <TradingViewChart bars={chart.bars} signal={detail} />
                </div>
              </div>
            )}
            <DebateTranscript experts={detail.experts} debate={detail.debate} />
            <div className="panel">
              <div className="row space" style={{ alignItems: "center" }}>
                <h2 style={{ margin: 0 }}>TradingView Pine Script</h2>
                <a
                  href={historyApi.pineUrl(detail.run_id)}
                  download={`investment_agent_run_${detail.run_id}.pine`}
                >
                  Download .pine
                </a>
              </div>
              <div className="small" style={{ marginBottom: 8 }}>
                Paste this into TradingView → Pine Editor → Add to chart to see the same signals on
                your TV charts (works on Essential plan — no alerts/webhooks needed).
              </div>
            </div>
          </>
        )}
      </main>

      {summaryOpenId != null && (
        <SignalSummaryModal
          signalId={summaryOpenId}
          onClose={() => setSummaryOpenId(null)}
          onOpenDetail={() => {
            const s = latest.find(x => x.id === summaryOpenId);
            if (s) setSelected(s.ticker);
          }}
        />
      )}
    </div>
  );
}
