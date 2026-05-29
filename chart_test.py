import yfinance as yf
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

ticker = yf.Ticker("AAPL")
data = ticker.history(period="6mo")

plt.figure(figsize=(12,6))

plt.plot(data.index, data["Close"])

plt.title("AAPL Price Chart")
plt.xlabel("Date")
plt.ylabel("Price")

plt.grid(True)

plt.show()