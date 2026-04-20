"""Technical indicators computed with pandas/numpy (no TA-Lib dep)."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _df(bars: list[dict[str, Any]]) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame()
    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    return line, sig, hist


def bollinger(close: pd.Series, period: int = 20, k: float = 2.0):
    ma = close.rolling(period).mean()
    sd = close.rolling(period).std()
    return ma + k * sd, ma, ma - k * sd


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def support_resistance(df: pd.DataFrame, window: int = 20) -> dict[str, float]:
    if df.empty:
        return {"support": None, "resistance": None}
    recent = df.tail(window * 3)
    return {
        "support": float(recent["low"].min()),
        "resistance": float(recent["high"].max()),
    }


def compute_indicators(bars: list[dict[str, Any]]) -> dict[str, Any]:
    df = _df(bars)
    if df.empty or len(df) < 30:
        return {"available": False}
    close = df["close"]
    high = df["high"]
    low = df["low"]
    rsi14 = rsi(close, 14)
    macd_line, macd_sig, macd_hist = macd(close)
    bb_u, bb_m, bb_l = bollinger(close)
    atr14 = atr(high, low, close)
    last = df.iloc[-1]
    sr = support_resistance(df)
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

    trend = "up" if (ma50 is not None and last["close"] > ma50) else "down"
    rsi_v = float(rsi14.iloc[-1]) if not np.isnan(rsi14.iloc[-1]) else None

    return {
        "available": True,
        "last_close": float(last["close"]),
        "last_volume": int(last["volume"]),
        "rsi14": rsi_v,
        "rsi_state": ("overbought" if rsi_v and rsi_v > 70 else "oversold" if rsi_v and rsi_v < 30 else "neutral"),
        "macd": {
            "line": float(macd_line.iloc[-1]),
            "signal": float(macd_sig.iloc[-1]),
            "hist": float(macd_hist.iloc[-1]),
            "crossover_up": bool(macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0),
            "crossover_down": bool(macd_hist.iloc[-1] < 0 and macd_hist.iloc[-2] >= 0),
        },
        "bollinger": {
            "upper": float(bb_u.iloc[-1]),
            "middle": float(bb_m.iloc[-1]),
            "lower": float(bb_l.iloc[-1]),
            "position": float((last["close"] - bb_l.iloc[-1]) / (bb_u.iloc[-1] - bb_l.iloc[-1])) if bb_u.iloc[-1] != bb_l.iloc[-1] else 0.5,
        },
        "atr14": float(atr14.iloc[-1]) if not np.isnan(atr14.iloc[-1]) else None,
        "ma20": float(ma20) if not np.isnan(ma20) else None,
        "ma50": float(ma50) if ma50 and not np.isnan(ma50) else None,
        "ma200": float(ma200) if ma200 and not np.isnan(ma200) else None,
        "trend": trend,
        "support": sr["support"],
        "resistance": sr["resistance"],
        "pct_from_52w_high": None,  # fundamentals provides 52w bounds
        "price_change_1d_pct": float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) > 1 else 0,
        "price_change_5d_pct": float((close.iloc[-1] / close.iloc[-6] - 1) * 100) if len(close) > 5 else 0,
        "price_change_20d_pct": float((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) > 20 else 0,
    }
