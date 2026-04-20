import { useEffect, useState } from "react";
import { watchlistApi } from "../api/client";
import type { WatchlistItem } from "../types";

interface Props {
  selected: string | null;
  onSelect: (ticker: string | null) => void;
  onChange: () => void;
}

export default function WatchlistPanel({ selected, onSelect, onChange }: Props) {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const data = await watchlistApi.list();
    setItems(data);
  }
  useEffect(() => { refresh(); }, []);

  async function add() {
    const t = input.trim().toUpperCase();
    if (!t) return;
    setLoading(true);
    try {
      await watchlistApi.add(t);
      setInput("");
      await refresh();
      onChange();
    } finally { setLoading(false); }
  }

  async function remove(t: string) {
    await watchlistApi.remove(t);
    await refresh();
    if (selected === t) onSelect(null);
    onChange();
  }

  return (
    <div className="panel">
      <h2>Watchlist</h2>
      <div className="row" style={{ marginBottom: 10 }}>
        <input
          placeholder="AAPL, NVDA, ..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && add()}
          style={{ flex: 1 }}
        />
        <button onClick={add} disabled={loading}>Add</button>
      </div>
      <div className="ticker-list">
        {items.length === 0 && <div className="small">No tickers yet. Add some above.</div>}
        {items.map(it => (
          <div
            key={it.ticker}
            className={`ticker-row ${selected === it.ticker ? "selected" : ""}`}
            onClick={() => onSelect(it.ticker)}
          >
            <span>{it.ticker}</span>
            <span className="rm" onClick={e => { e.stopPropagation(); remove(it.ticker); }}>✕</span>
          </div>
        ))}
      </div>
    </div>
  );
}
