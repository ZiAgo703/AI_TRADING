import os
import yfinance as yf
import ta
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

stocks = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"]

chart_dir = "us_charts"
os.makedirs(chart_dir, exist_ok=True)

results = []

for symbol in stocks:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="3mo")

    data["RSI"] = ta.momentum.RSIIndicator(
        data["Close"], window=14
    ).rsi()

    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA60"] = data["Close"].rolling(window=60).mean()

    latest = data.iloc[-1]

    if latest["RSI"] < 30 and latest["Close"] > latest["MA20"]:
        signal = "BUY"
    elif latest["RSI"] > 70:
        signal = "CAUTION"
    elif latest["Close"] < latest["MA60"]:
        signal = "SELL"
    else:
        signal = "HOLD"

    results.append({
        "종목": symbol,
        "현재가": round(latest["Close"], 2),
        "RSI": round(latest["RSI"], 2),
        "MA20": round(latest["MA20"], 2),
        "MA60": round(latest["MA60"], 2),
        "신호": signal
    })

    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data["Close"], label="Close")
    plt.plot(data.index, data["MA20"], label="MA20")
    plt.plot(data.index, data["MA60"], label="MA60")
    plt.title(f"{symbol} — {signal}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(chart_dir, f"{symbol}.png"))
    plt.close()

df = pd.DataFrame(results)

print("\n===== 종목 분석 결과 =====")
print(df)
print(f"\n차트 저장 완료: {chart_dir} 폴더")