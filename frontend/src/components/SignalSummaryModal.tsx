import { useEffect, useState } from "react";
import { signalsApi } from "../api/client";
import type { Signal } from "../types";

interface Props {
  signalId: number;
  onClose: () => void;
  onOpenDetail?: () => void;
}

export default function SignalSummaryModal({ signalId, onClose, onOpenDetail }: Props) {
  const [detail, setDetail] = useState<Signal | null>(null);

  useEffect(() => {
    signalsApi.detail(signalId).then(setDetail);
  }, [signalId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-head">
          <h2 style={{ margin: 0 }}>
            {detail?.ticker || "…"}{" "}
            {detail && <span className={`badge ${detail.action}`}>{detail.action}</span>}
          </h2>
          <button className="secondary icon" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {!detail && <div className="small">Loading…</div>}

        {detail && (
          <div className="modal-body">
            <section>
              <h3>TL;DR</h3>
              <p style={{ whiteSpace: "pre-wrap" }}>
                {detail.summary || detail.thesis}
              </p>
            </section>

            <section>
              <h3>Analysis</h3>
              <p style={{ whiteSpace: "pre-wrap" }}>{detail.thesis}</p>
              {detail.risks && (
                <>
                  <h3 style={{ marginTop: 8 }}>Risks</h3>
                  <p style={{ whiteSpace: "pre-wrap" }}>{detail.risks}</p>
                </>
              )}
            </section>

            <section>
              <h3>Committee debate</h3>
              {detail.debate_summary && (
                <p style={{ whiteSpace: "pre-wrap", marginBottom: 10 }}>
                  {detail.debate_summary}
                </p>
              )}
              <div className="expert-chips">
                {(detail.experts || []).map((e, i) => (
                  <div key={i} className="expert-chip">
                    <div className="row space" style={{ alignItems: "center" }}>
                      <b>{e.expert}</b>
                      <span>
                        <span className={`badge ${e.action}`}>{e.action}</span>{" "}
                        <span className="small num">{(e.confidence * 100).toFixed(0)}%</span>
                      </span>
                    </div>
                    <div className="small" style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>
                      {e.thesis}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {detail.qc_notes && (
              <section>
                <h3>QC notes</h3>
                <p className="small" style={{ whiteSpace: "pre-wrap" }}>{detail.qc_notes}</p>
              </section>
            )}

            <div className="row" style={{ justifyContent: "flex-end", marginTop: 12 }}>
              {onOpenDetail && (
                <button onClick={() => { onOpenDetail(); onClose(); }}>
                  Open full detail view
                </button>
              )}
              <button className="secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
