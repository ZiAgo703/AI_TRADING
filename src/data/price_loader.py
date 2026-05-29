import pandas as pd
import yfinance as yf


def load_price(ticker: str, period: str = "6mo") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period)
    # yfinance sometimes appends the current day with NaN Close
    # (market not yet closed). Drop those rows so iloc[-1] is always valid.
    return df.dropna(subset=["Close"]) if not df.empty else df
