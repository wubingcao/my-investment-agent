import type { Signal } from "../types";

export default function SignalCard({ signal, onOpen }: { signal: Signal; onOpen?: () => void }) {
  const fmt = (n: number | null | undefined, d = 2) => (n == null ? "—" : n.toFixed(d));
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`;
  return (
    <div className="panel" onClick={onOpen} style={{ cursor: onOpen ? "pointer" : "default" }}>
      <div className="row space" style={{ alignItems: "center", marginBottom: 8 }}>
        <h2 style={{ margin: 0 }}>
          {signal.ticker} <span className={`badge ${signal.action}`}>{signal.action}</span>
        </h2>
        <div className="small">
          conf <b className="num">{pct(signal.confidence)}</b>
          {" · size "}<b className="num">{signal.target_pct.toFixed(1)}%</b>
          {signal.qc_passed ? (
            <span className="badge" style={{ marginLeft: 6, background: "rgba(61,220,151,0.15)", color: "var(--buy)" }}>QC ✓</span>
          ) : (
            <span className="badge warn" style={{ marginLeft: 6 }}>QC ✗</span>
          )}
        </div>
      </div>

      <div className="signal-card">
        <div>
          <div className="kv">
            <div className="k">Entry range</div>
            <div className="num">{fmt(signal.buy_low)} – {fmt(signal.buy_high)}</div>
            <div className="k">Exit range</div>
            <div className="num">{fmt(signal.sell_low)} – {fmt(signal.sell_high)}</div>
            <div className="k">Stop loss</div>
            <div className="num">{fmt(signal.stop_loss)}</div>
            <div className="k">Horizon</div>
            <div>{signal.time_horizon}</div>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, whiteSpace: "pre-wrap" }}>
            <b>Thesis.</b> {signal.thesis}
            {signal.risks ? <><br /><br /><b>Risks.</b> {signal.risks}</> : null}
          </div>
        </div>
      </div>
      <div className="small" style={{ marginTop: 8 }}>
        {signal.debate_summary}
      </div>
    </div>
  );
}
