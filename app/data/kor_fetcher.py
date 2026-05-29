"""Korean market index fetcher.

Provides KOSPI / KOSDAQ index data via yfinance — no KRX login required.
Individual stock OHLCV is handled by src.data.price_loader.
"""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_INDEX_TICKERS: dict[str, str] = {
    "KOSPI":  "^KS11",
    "KOSDAQ": "^KQ11",
}


def fetch_index_ohlcv(name: str, months: int = 1) -> pd.DataFrame:
    """Fetch OHLCV for a Korean index by name ("KOSPI" or "KOSDAQ").

    Returns empty DataFrame on failure.
    """
    yf_ticker = _INDEX_TICKERS.get(name)
    if not yf_ticker:
        logger.warning("알 수 없는 지수: %s", name)
        return pd.DataFrame()

    try:
        period_str = f"{months}mo" if months <= 11 else "1y"
        df = yf.Ticker(yf_ticker).history(period=period_str)
        if df.empty or "Close" not in df.columns:
            return pd.DataFrame()
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        return df[df["Close"] > 0]
    except Exception as exc:
        logger.debug("지수 수집 실패 %s: %s", yf_ticker, exc)
        return pd.DataFrame()


def get_market_indices() -> dict[str, dict]:
    """Return latest close + day-change % for KOSPI and KOSDAQ.

    Returns empty dict only when yfinance fails for both indices.
    Each entry: {"close": float, "change_pct": float}
    """
    result: dict[str, dict] = {}

    for name in _INDEX_TICKERS:
        df = fetch_index_ohlcv(name, months=1)
        if df.empty:
            logger.warning("지수 데이터 없음: %s", name)
            continue
        close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else close
        change_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else 0.0
        result[name] = {"close": close, "change_pct": change_pct}

    return result
