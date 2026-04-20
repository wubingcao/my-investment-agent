from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Watchlist(Base):
    __tablename__ = "watchlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(Text, default="")


class AnalysisRun(Base):
    __tablename__ = "analysis_run"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger: Mapped[str] = mapped_column(String(32))  # "on_demand" | "scheduled"
    tickers: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|done|error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    signals: Mapped[list["Signal"]] = relationship(back_populates="run", cascade="all, delete")


class Signal(Base):
    __tablename__ = "signal"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("analysis_run.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    action: Mapped[str] = mapped_column(String(8))  # BUY|SELL|HOLD
    confidence: Mapped[float] = mapped_column(Float)
    buy_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    buy_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_pct: Mapped[float] = mapped_column(Float, default=0.0)  # % of portfolio
    time_horizon: Mapped[str] = mapped_column(String(32), default="swing")  # day|swing|position
    summary: Mapped[str] = mapped_column(Text, default="")
    thesis: Mapped[str] = mapped_column(Text)
    risks: Mapped[str] = mapped_column(Text)
    debate_summary: Mapped[str] = mapped_column(Text)
    qc_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    qc_notes: Mapped[str] = mapped_column(Text, default="")
    raw: Mapped[dict] = mapped_column(JSON)  # experts' verdicts + debate transcript
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped[AnalysisRun] = relationship(back_populates="signals")


class SignalOutcome(Base):
    """Populated by the performance evaluator (phase 2)."""
    __tablename__ = "signal_outcome"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signal.id"), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    horizon_days: Mapped[int] = mapped_column(Integer, default=5)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    hit_target: Mapped[bool] = mapped_column(Boolean, default=False)
    hit_stop: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class Setting(Base):
    __tablename__ = "setting"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
