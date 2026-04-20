import { useEffect, useState } from "react";
import { settingsApi } from "../api/client";
import type { RiskSettings } from "../types";

const presets: Record<string, Partial<RiskSettings>> = {
  conservative: { max_position_pct: 8, default_stop_loss_pct: 4, portfolio_drawdown_alert_pct: 10 },
  moderate:     { max_position_pct: 15, default_stop_loss_pct: 7, portfolio_drawdown_alert_pct: 20 },
  aggressive:   { max_position_pct: 25, default_stop_loss_pct: 10, portfolio_drawdown_alert_pct: 30 },
};

export default function SettingsPage() {
  const [risk, setRisk] = useState<RiskSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { settingsApi.getRisk().then(setRisk); }, []);

  if (!risk) return <div className="content"><div className="panel"><div className="small">Loading…</div></div></div>;

  function update<K extends keyof RiskSettings>(k: K, v: RiskSettings[K]) {
    setRisk(prev => prev ? { ...prev, [k]: v } : prev);
  }

  async function save() {
    if (!risk) return;
    setSaving(true); setMsg("");
    try {
      const out = await settingsApi.setRisk(risk);
      setRisk(out);
      setMsg("Saved.");
    } catch (e: any) {
      setMsg(`Error: ${e?.message ?? "save failed"}`);
    } finally { setSaving(false); }
  }

  function applyPreset(name: "conservative" | "moderate" | "aggressive") {
    if (!risk) return;
    setRisk({ ...risk, risk_profile: name, ...presets[name] } as RiskSettings);
  }

  return (
    <div className="content" style={{ maxWidth: 720, margin: "0 auto" }}>
      <div className="panel">
        <h2>Risk settings</h2>
        <div className="small" style={{ marginBottom: 12 }}>
          These drive Portfolio Manager sizing, QC thresholds, and stop-loss defaults.
        </div>

        <div className="row" style={{ marginBottom: 12 }}>
          {(["conservative", "moderate", "aggressive"] as const).map(p => (
            <button
              key={p}
              className={risk.risk_profile === p ? "" : "secondary"}
              onClick={() => applyPreset(p)}
              style={{ textTransform: "capitalize" }}
            >
              {p}
            </button>
          ))}
        </div>

        <div className="kv" style={{ gap: 10, rowGap: 10 }}>
          <label className="k">Total capital (USD)</label>
          <input type="number" value={risk.total_capital_usd}
            onChange={e => update("total_capital_usd", Number(e.target.value))} />
          <label className="k">Max position (%)</label>
          <input type="number" step="0.5" value={risk.max_position_pct}
            onChange={e => update("max_position_pct", Number(e.target.value))} />
          <label className="k">Max concurrent positions</label>
          <input type="number" value={risk.max_concurrent_positions}
            onChange={e => update("max_concurrent_positions", Number(e.target.value))} />
          <label className="k">Default stop-loss (%)</label>
          <input type="number" step="0.1" value={risk.default_stop_loss_pct}
            onChange={e => update("default_stop_loss_pct", Number(e.target.value))} />
          <label className="k">Portfolio DD alert (%)</label>
          <input type="number" step="0.5" value={risk.portfolio_drawdown_alert_pct}
            onChange={e => update("portfolio_drawdown_alert_pct", Number(e.target.value))} />
        </div>

        <div className="row" style={{ marginTop: 16 }}>
          <button onClick={save} disabled={saving}>Save</button>
          {msg && <span className="small" style={{ alignSelf: "center" }}>{msg}</span>}
        </div>
      </div>

      <div className="panel">
        <h2>Scheduled jobs</h2>
        <div className="small">
          Configured via <code>backend/.env</code>:
          <ul>
            <li><b>Daily scan</b> — watchlist analysis each weekday morning</li>
            <li><b>Daily perf-eval</b> — scores old signals against subsequent price action</li>
            <li><b>Weekly learnings</b> — Claude writes lessons markdown from outcomes</li>
            <li><b>Monthly skills</b> — distills recurring patterns into reusable playbooks</li>
          </ul>
          Files land in <code>knowledge_base/</code>.
        </div>
      </div>
    </div>
  );
}
