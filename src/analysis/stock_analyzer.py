import math
import pandas as pd

from src.data.ticker_loader import load_tickers
from src.data.price_loader import load_price
from src.indicators.technical import calculate_indicators, calc_returns
from src.scoring.stock_scorer import score_stock, classify_stock


class StockAnalyzer:
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir

    def run(self) -> tuple[pd.DataFrame, dict]:
        tickers = load_tickers(self.config_dir)
        results = []
        raw_data = {}

        for name, info in tickers.items():
            symbol = info["ticker"]
            market = info["market"]
            currency = info["currency"]

            print(f"  분석 중: {name} ({symbol})")

            try:
                data = load_price(symbol, period="6mo")

                if data.empty or len(data) < 60:
                    print(f"    데이터 부족: {name} ({len(data)}일)")
                    continue

                data = calculate_indicators(data)
                returns = calc_returns(data)
                latest = data.iloc[-1]

                scoring = score_stock(latest, returns)
                category, action = classify_stock(latest, scoring["score"])

                def r(val, digits=2):
                    v = float(val)
                    return round(v, digits) if not math.isnan(v) else None

                results.append({
                    "종목": name,
                    "티커": symbol,
                    "시장": market,
                    "통화": currency,
                    "현재가": r(latest["Close"]),
                    "RSI": r(latest["RSI"]),
                    "MA20": r(latest["MA20"]),
                    "MA60": r(latest["MA60"]),
                    "MA120": r(latest["MA120"]),
                    "MACD": r(latest["MACD"], 4),
                    "MACD_Signal": r(latest["MACD_Signal"], 4),
                    "BB_Upper": r(latest["BB_Upper"]),
                    "BB_Middle": r(latest["BB_Middle"]),
                    "BB_Lower": r(latest["BB_Lower"]),
                    "1개월수익률(%)": round(returns["1m"], 2),
                    "3개월수익률(%)": round(returns["3m"], 2),
                    "6개월수익률(%)": round(returns["6m"], 2),
                    "거래량비율": round(scoring["volume_ratio"], 2),
                    "변동성(%)": round(returns["volatility"], 2),
                    "점수": scoring["score"],
                    "점수상세": scoring["breakdown"],
                    "분류": category,
                    "추천행동": action,
                })

                raw_data[name] = data

            except Exception as e:
                print(f"    오류: {name} / {e}")

        df = (
            pd.DataFrame(results)
            .sort_values("점수", ascending=False)
            .reset_index(drop=True)
        )
        return df, raw_data
