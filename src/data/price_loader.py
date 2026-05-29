"""OHLCV data loader.

Korean .KS tickers: pykrx first (no login), yfinance fallback.
US tickers: yfinance only.

pykrx prints a Korean "login failed" warning to stdout on every import.
We silence it because the public OHLCV endpoint works without credentials.
"""
from __future__ import annotations

import contextlib
import io
import re
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def _import_pykrx():
    """Import pykrx while swallowing its startup login warning."""
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            from pykrx import stock as _s
        return _s, True
    except ImportError:
        return None, False


_krx, _PYKRX_OK = _import_pykrx()

_KS_RE = re.compile(r"^(\d{6})\.KS$", re.IGNORECASE)


def _ks_code(ticker: str) -> str | None:
    """Extract 6-digit KRX code from a .KS ticker, or None for non-KR tickers."""
    m = _KS_RE.match(ticker)
    return m.group(1) if m else None


def _period_to_months(period: str) -> int:
    if period.endswith("mo"):
        return int(period[:-2])
    if period.endswith("y"):
        return int(period[:-1]) * 12
    return 6


def _date_range(months: int) -> tuple[str, str]:
    end = datetime.today()
    start = end - timedelta(days=months * 31)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _normalize_pykrx(df: pd.DataFrame) -> pd.DataFrame:
    """Rename pykrx Korean columns → standard OHLCV names.

    pykrx also returns 등락률 (change %) which is dropped here.
    """
    col_map = {
        "시가": "Open", "고가": "High", "저가": "Low",
        "종가": "Close", "거래량": "Volume",
    }
    df = df.rename(columns=col_map)
    keep = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in df.columns]
    if not keep:
        return pd.DataFrame()
    df = df[keep].copy()
    df.index = pd.to_datetime(df.index)
    df = df[df["Close"] > 0]
    return df


def load_price(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch OHLCV for a single ticker.

    Korean .KS tickers → pykrx (KRX public API, no login required).
    Falls back to yfinance on any failure or when pykrx is not installed.
    """
    kr_code = _ks_code(ticker)

    if kr_code and _PYKRX_OK:
        try:
            start, end = _date_range(_period_to_months(period))
            raw = _krx.get_market_ohlcv_by_date(start, end, kr_code)
            df = _normalize_pykrx(raw)
            if not df.empty:
                return df
        except Exception:
            pass

    return yf.Ticker(ticker).history(period=period)
