import yfinance as yf
import ta

ticker = yf.Ticker("AAPL")
data = ticker.history(period="3mo")

data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
data["MA20"] = data["Close"].rolling(window=20).mean()
data["MA60"] = data["Close"].rolling(window=60).mean()

latest = data.iloc[-1]

print("===== AAPL 분석 결과 =====")
print(f"현재가: {latest['Close']:.2f}")
print(f"RSI: {latest['RSI']:.2f}")
print(f"MA20: {latest['MA20']:.2f}")
print(f"MA60: {latest['MA60']:.2f}")

if latest["RSI"] < 30 and latest["Close"] > latest["MA20"]:
    signal = "BUY"
elif latest["RSI"] > 70:
    signal = "CAUTION / TAKE PROFIT"
elif latest["Close"] < latest["MA60"]:
    signal = "SELL / RISK OFF"
else:
    signal = "HOLD"

print(f"신호: {signal}")