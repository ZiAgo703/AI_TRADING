import pandas as pd
import yfinance as yf


def load_price(ticker: str, period: str = "6mo") -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period)
