import type { Signal } from "../types";

interface Props {
  signal: Signal;
  onOpenDetail: () => void;
  onOpenSummary: () => void;
}

export default function SignalTile({ signal, onOpenDetail, onOpenSummary }: Props) {
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`;
  const isActionable = signal.action === "BUY" || signal.action === "SELL";

  return (
    <div className="signal-tile" onClick={onOpenDetail} role="button" tabIndex={0}>
      <div className="tile-head">
        <div className="tile-ticker">{signal.ticker}</div>
        <button
          className="tile-info"
          title="View analysis & debate summary"
          aria-label={`${signal.ticker} summary`}
          onClick={e => { e.stopPropagation(); onOpenSummary(); }}
        >
          ⓘ
        </button>
      </div>

      <div className={`tile-action badge ${signal.action}`}>{signal.action}</div>

      <div className="tile-stats">
        <div className="stat">
          <div className="stat-label">Conf</div>
          <div className="stat-value num">{pct(signal.confidence)}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Size</div>
          <div className="stat-value num">
            {isActionable ? `${signal.target_pct.toFixed(1)}%` : "—"}
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">QC</div>
          <div className="stat-value">
            {signal.qc_passed ? (
              <span style={{ color: "var(--buy)" }}>✓</span>
            ) : (
              <span style={{ color: "var(--warning)" }}>✗</span>
            )}
          </div>
        </div>
      </div>

      {isActionable && (signal.buy_low != null || signal.sell_low != null) && (
        <div className="tile-bands">
          {signal.action === "BUY" && signal.buy_low != null && signal.buy_high != null && (
            <div><span className="small">Entry</span> <b className="num">{signal.buy_low.toFixed(2)} – {signal.buy_high.toFixed(2)}</b></div>
          )}
          {signal.action === "SELL" && signal.sell_low != null && signal.sell_high != null && (
            <div><span className="small">Exit</span> <b className="num">{signal.sell_low.toFixed(2)} – {signal.sell_high.toFixed(2)}</b></div>
          )}
          {signal.stop_loss != null && (
            <div><span className="small">Stop</span> <b className="num">{signal.stop_loss.toFixed(2)}</b></div>
          )}
        </div>
      )}

      <div className="tile-summary">
        {signal.summary || signal.thesis?.slice(0, 140) || "No summary available"}
      </div>
    </div>
  );
}
