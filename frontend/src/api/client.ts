import axios from "axios";
import type { AnalysisRun, ChartResponse, Horizon, RiskSettings, Signal, WatchlistItem } from "../types";

const api = axios.create({ baseURL: "/api", timeout: 300_000 });

export const watchlistApi = {
  list: () => api.get<WatchlistItem[]>("/watchlist").then(r => r.data),
  add:  (ticker: string, notes = "") => api.post("/watchlist", { ticker, notes }).then(r => r.data),
  remove: (ticker: string) => api.delete(`/watchlist/${ticker}`).then(r => r.data),
};

export const analyzeApi = {
  run: (tickers: string[], time_horizon: Horizon = "swing") =>
    api.post<{ run_id: number; status: string }>("/analyze", { tickers, time_horizon }).then(r => r.data),
  runAsync: (tickers: string[], time_horizon: Horizon = "swing") =>
    api.post<{ status: string }>("/analyze/async", { tickers, time_horizon }).then(r => r.data),
};

export const signalsApi = {
  latest: (limit = 50) => api.get<Signal[]>("/signals/latest", { params: { limit } }).then(r => r.data),
  byTicker: (ticker: string, limit = 20) =>
    api.get<Signal[]>(`/signals/by-ticker/${ticker}`, { params: { limit } }).then(r => r.data),
  detail: (id: number) => api.get<Signal>(`/signals/${id}`).then(r => r.data),
  chart: (id: number, period = "6mo", interval = "1d") =>
    api.get<ChartResponse>(`/signals/${id}/chart`, { params: { period, interval } }).then(r => r.data),
};

export const historyApi = {
  runs: (limit = 30) => api.get<AnalysisRun[]>("/history/runs", { params: { limit } }).then(r => r.data),
  run: (id: number) => api.get<AnalysisRun>(`/history/runs/${id}`).then(r => r.data),
  pineUrl: (id: number) => `/api/history/runs/${id}/pine`,
};

export const settingsApi = {
  getRisk: () => api.get<RiskSettings>("/settings/risk").then(r => r.data),
  setRisk: (v: RiskSettings) => api.put<RiskSettings>("/settings/risk", v).then(r => r.data),
};
