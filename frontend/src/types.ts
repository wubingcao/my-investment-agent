export type Action = "BUY" | "SELL" | "HOLD";
export type Horizon = "day" | "swing" | "position";

export interface WatchlistItem {
  ticker: string;
  notes: string;
  added_at: string;
}

export interface RiskSettings {
  max_position_pct: number;
  max_concurrent_positions: number;
  default_stop_loss_pct: number;
  portfolio_drawdown_alert_pct: number;
  risk_profile: "conservative" | "moderate" | "aggressive";
  total_capital_usd: number;
}

export interface ExpertVerdict {
  expert: string;
  action: Action;
  confidence: number;
  thesis: string;
  key_points: string[];
  risks: string[];
  price_target: number | null;
  entry_range: [number, number] | null;
  exit_range: [number, number] | null;
}

export interface DebateTurn {
  round: number;
  expert: string;
  stance: string;
  argument: string;
  rebuttal_to: string | null;
}

export interface Signal {
  id: number;
  run_id: number;
  ticker: string;
  action: Action;
  confidence: number;
  buy_low: number | null;
  buy_high: number | null;
  sell_low: number | null;
  sell_high: number | null;
  stop_loss: number | null;
  target_pct: number;
  time_horizon: string;
  summary?: string;
  thesis: string;
  risks: string;
  debate_summary: string;
  qc_passed: boolean;
  qc_notes: string;
  created_at: string;
  experts?: ExpertVerdict[];
  debate?: DebateTurn[];
  qc?: any;
  brief_snapshot?: any;
}

export interface AnalysisRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  trigger: string;
  tickers: string[];
  status: string;
  error: string | null;
  signals?: Array<Pick<Signal, "id" | "ticker" | "action" | "confidence" | "target_pct" | "qc_passed" | "thesis">>;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  ticker: string;
  period: string;
  interval: string;
  bars: Bar[];
  indicators: any;
  signal: Signal;
}
