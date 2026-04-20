from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    ticker: str
    notes: str = ""


class RiskSettings(BaseModel):
    max_position_pct: float = Field(15.0, ge=0, le=100)
    max_concurrent_positions: int = Field(10, ge=1, le=50)
    default_stop_loss_pct: float = Field(7.0, ge=0.1, le=50)
    portfolio_drawdown_alert_pct: float = Field(20.0, ge=1, le=100)
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    total_capital_usd: float = Field(100_000.0, ge=0)


class AnalyzeRequest(BaseModel):
    tickers: list[str]
    time_horizon: Literal["day", "swing", "position"] = "swing"
    notes: str = ""


class ExpertVerdict(BaseModel):
    expert: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    thesis: str
    key_points: list[str]
    risks: list[str]
    price_target: float | None = None
    entry_range: list[float] | None = None  # [low, high]
    exit_range: list[float] | None = None


class DebateTurn(BaseModel):
    round: int
    expert: str
    stance: str        # agree / disagree / refine
    argument: str
    rebuttal_to: str | None = None


class SignalOut(BaseModel):
    id: int | None = None
    ticker: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    buy_low: float | None = None
    buy_high: float | None = None
    sell_low: float | None = None
    sell_high: float | None = None
    stop_loss: float | None = None
    target_pct: float = 0.0
    time_horizon: str = "swing"
    summary: str = ""
    thesis: str
    risks: str
    debate_summary: str
    qc_passed: bool = False
    qc_notes: str = ""
    experts: list[ExpertVerdict] = []
    debate: list[DebateTurn] = []
    created_at: datetime | None = None


class AnalysisRunOut(BaseModel):
    id: int
    started_at: datetime
    finished_at: datetime | None
    trigger: str
    tickers: list[str]
    status: str
    error: str | None = None
    signals: list[SignalOut] = []


class PortfolioSummary(BaseModel):
    total_capital_usd: float
    allocated_pct: float
    positions: list[dict[str, Any]]
    cash_pct: float


class QcReport(BaseModel):
    passed: bool
    issues: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {}
