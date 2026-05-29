import os
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "AMD": "AMD",
    "Apple": "AAPL",
    "Google": "GOOGL",
}

chart_dir = "charts"
os.makedirs(chart_dir, exist_ok=True)

results = []

for name, symbol in stocks.items():
    try:
        data = yf.Ticker(symbol).history(period="6mo")

        if data.empty or len(data) < 60:
            print(f"{name} 데이터 부족")
            continue

        data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["MA60"] = data["Close"].rolling(window=60).mean()

        latest = data.iloc[-1]
        start_price = data.iloc[0]["Close"]

        return_6m = ((latest["Close"] - start_price) / start_price) * 100
        volatility = data["Close"].pct_change().std() * 100

        score = 0

        if latest["Close"] > latest["MA20"]:
            score += 2
        if latest["Close"] > latest["MA60"]:
            score += 2

        if 40 <= latest["RSI"] <= 65:
            score += 2
        elif 65 < latest["RSI"] <= 70:
            score += 1
        elif latest["RSI"] > 75:
            score -= 2

        if return_6m > 20:
            score += 2
        elif return_6m > 5:
            score += 1

        if volatility > 4:
            score -= 1

        if latest["RSI"] > 70:
            signal = "과열주의"
            action = "눌림목 대기"
        elif latest["Close"] < latest["MA60"]:
            signal = "약세주의"
            action = "관망"
        elif score >= 6:
            signal = "관심강함"
            action = "분할매수 후보"
        elif score >= 4:
            signal = "관심"
            action = "추적관찰"
        else:
            signal = "관망"
            action = "매수 보류"

        results.append({
            "종목": name,
            "티커": symbol,
            "현재가": round(latest["Close"], 2),
            "RSI": round(latest["RSI"], 2),
            "MA20": round(latest["MA20"], 2),
            "MA60": round(latest["MA60"], 2),
            "6개월수익률(%)": round(return_6m, 2),
            "변동성(%)": round(volatility, 2),
            "점수": score,
            "판단": signal,
            "추천행동": action
        })

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data["Close"], label="Close")
        plt.plot(data.index, data["MA20"], label="MA20")
        plt.plot(data.index, data["MA60"], label="MA60")

        plt.title(f"{name} ({symbol}) Price Chart")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)

        chart_path = os.path.join(chart_dir, f"{symbol.replace('.', '_')}_{name}.png")
        plt.savefig(chart_path)
        plt.close()

    except Exception as e:
        print(f"{name} 오류 발생: {e}")

df = pd.DataFrame(results)
df = df.sort_values(by="점수", ascending=False)

csv_file = "stock_compare_result.csv"
df.to_csv(csv_file, index=False, encoding="utf-8-sig")

print("\n===== 한국 + 미국 관심 종목 비교 =====")
print(df.to_string(index=False))

print(f"\nCSV 저장 완료: {csv_file}")
print(f"차트 저장 폴더: {chart_dir}")