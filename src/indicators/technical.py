import pandas as pd
import ta


def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    close = data["Close"]
    volume = data["Volume"]

    # Moving averages
    data["MA20"] = close.rolling(20).mean()
    data["MA60"] = close.rolling(60).mean()
    data["MA120"] = close.rolling(120).mean()

    # RSI
    data["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # MACD
    macd = ta.trend.MACD(close)
    data["MACD"] = macd.macd()
    data["MACD_Signal"] = macd.macd_signal()
    data["MACD_Hist"] = macd.macd_diff()

    # Bollinger Bands (20-day, 2σ)
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    data["BB_Upper"] = bb.bollinger_hband()
    data["BB_Middle"] = bb.bollinger_mavg()
    data["BB_Lower"] = bb.bollinger_lband()

    # Volume
    data["Volume_MA20"] = volume.rolling(20).mean()

    return data


def calc_returns(data: pd.DataFrame) -> dict:
    close = data["Close"]
    current = close.iloc[-1]
    n = len(data)

    ret_1m = (current - close.iloc[-20]) / close.iloc[-20] * 100 if n >= 20 else 0.0
    ret_3m = (current - close.iloc[-60]) / close.iloc[-60] * 100 if n >= 60 else 0.0
    ret_6m = (current - close.iloc[0]) / close.iloc[0] * 100
    volatility = close.pct_change().std() * 100

    return {"1m": ret_1m, "3m": ret_3m, "6m": ret_6m, "volatility": volatility}
