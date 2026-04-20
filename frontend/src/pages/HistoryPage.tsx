import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { historyApi } from "../api/client";
import type { AnalysisRun } from "../types";

export default function HistoryPage() {
  const { runId } = useParams<{ runId?: string }>();
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [detail, setDetail] = useState<AnalysisRun | null>(null);

  useEffect(() => {
    historyApi.runs(50).then(setRuns);
  }, []);

  useEffect(() => {
    if (runId) historyApi.run(Number(runId)).then(setDetail);
  }, [runId]);

  return (
    <div className="main">
      <aside className="sidebar">
        <div className="panel">
          <h2>Analysis runs</h2>
          {runs.length === 0 && <div className="small">No runs yet.</div>}
          <div className="ticker-list">
            {runs.map(r => (
              <Link
                key={r.id}
                to={`/history/${r.id}`}
                className={`ticker-row ${String(r.id) === runId ? "selected" : ""}`}
                style={{ color: "inherit" }}
              >
                <span>#{r.id} · {r.trigger}</span>
                <span className="small">{new Date(r.started_at).toLocaleString()}</span>
              </Link>
            ))}
          </div>
        </div>
      </aside>

      <main className="content">
        {!detail && <div className="panel"><div className="small">Select a run.</div></div>}
        {detail && (
          <>
            <div className="panel">
              <h2>Run #{detail.id} · {detail.trigger}</h2>
              <div className="kv">
                <div className="k">Started</div><div>{new Date(detail.started_at).toLocaleString()}</div>
                <div className="k">Finished</div><div>{detail.finished_at ? new Date(detail.finished_at).toLocaleString() : "—"}</div>
                <div className="k">Status</div><div>{detail.status}</div>
                <div className="k">Tickers</div><div>{detail.tickers.join(", ")}</div>
              </div>
              {detail.error && <pre style={{ color: "var(--sell)" }}>{detail.error}</pre>}
              <div style={{ marginTop: 8 }}>
                <a href={historyApi.pineUrl(detail.id)} download={`run_${detail.id}.pine`}>
                  Download Pine Script
                </a>
              </div>
            </div>

            <div className="panel">
              <h2>Signals in this run</h2>
              {!detail.signals?.length ? (
                <div className="small">No signals recorded.</div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ textAlign: "left", color: "var(--text-dim)" }}>
                      <th style={th}>Ticker</th>
                      <th style={th}>Action</th>
                      <th style={th}>Conf</th>
                      <th style={th}>Size</th>
                      <th style={th}>QC</th>
                      <th style={th}>Thesis</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.signals.map(s => (
                      <tr key={s.id} style={{ borderTop: "1px solid var(--border)" }}>
                        <td style={td}><b>{s.ticker}</b></td>
                        <td style={td}><span className={`badge ${s.action}`}>{s.action}</span></td>
                        <td style={td}>{(s.confidence * 100).toFixed(0)}%</td>
                        <td style={td}>{s.target_pct.toFixed(1)}%</td>
                        <td style={td}>{s.qc_passed ? "✓" : "✗"}</td>
                        <td style={{ ...td, maxWidth: 520 }}>{s.thesis}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

const th: React.CSSProperties = { padding: "8px 6px", fontWeight: 600 };
const td: React.CSSProperties = { padding: "8px 6px", verticalAlign: "top" };
