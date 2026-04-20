import type { DebateTurn, ExpertVerdict } from "../types";

export default function DebateTranscript({
  experts,
  debate,
}: {
  experts?: ExpertVerdict[];
  debate?: DebateTurn[];
}) {
  if (!debate?.length && !experts?.length) {
    return <div className="panel"><h2>Debate transcript</h2><div className="small">No debate recorded.</div></div>;
  }

  const byRound = new Map<number, DebateTurn[]>();
  (debate || []).forEach(d => {
    const arr = byRound.get(d.round) || [];
    arr.push(d);
    byRound.set(d.round, arr);
  });
  const rounds = [...byRound.keys()].sort();

  return (
    <div className="panel">
      <h2>Committee debate</h2>

      <h3>Final verdicts</h3>
      <div className="col" style={{ gap: 6, marginBottom: 12 }}>
        {(experts || []).map((e, i) => (
          <div key={i} className="row space" style={{ alignItems: "flex-start" }}>
            <div style={{ flex: 1 }}>
              <b>{e.expert}</b> <span className={`badge ${e.action}`}>{e.action}</span>{" "}
              <span className="small">conf {(e.confidence * 100).toFixed(0)}%</span>
              <div className="small" style={{ marginTop: 2, whiteSpace: "pre-wrap" }}>{e.thesis}</div>
            </div>
          </div>
        ))}
      </div>

      {rounds.map(r => (
        <div key={r}>
          <h3>Round {r}</h3>
          {byRound.get(r)!.map((t, idx) => (
            <div key={idx} className={`debate-turn ${t.stance}`}>
              <div className="meta">
                <b>{t.expert}</b> · {t.stance}
                {t.rebuttal_to ? <> · rebutting <b>{t.rebuttal_to}</b></> : null}
              </div>
              <div style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>{t.argument}</div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
