import os
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

stocks = {
    # 한국
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",

    # 미국
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Apple": "AAPL",
    "Google": "GOOGL",
    "AMD": "AMD",
    "Tesla": "TSLA",
    "Amazon": "AMZN",
    "Meta": "META",
}

chart_dir = "rank_charts"
os.makedirs(chart_dir, exist_ok=True)

results = []

for name, symbol in stocks.items():
    try:
        data = yf.Ticker(symbol).history(period="6mo")

        if data.empty or len(data) < 60:
            continue

        data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
        data["MA20"] = data["Close"].rolling(20).mean()
        data["MA60"] = data["Close"].rolling(60).mean()
        data["Volume_MA20"] = data["Volume"].rolling(20).mean()

        latest = data.iloc[-1]
        prev = data.iloc[-2]
        start = data.iloc[0]

        return_6m = ((latest["Close"] - start["Close"]) / start["Close"]) * 100
        return_1m = ((latest["Close"] - data.iloc[-20]["Close"]) / data.iloc[-20]["Close"]) * 100
        volume_ratio = latest["Volume"] / latest["Volume_MA20"]
        volatility = data["Close"].pct_change().std() * 100

        score = 0

        if latest["Close"] > latest["MA20"]:
            score += 2
        if latest["Close"] > latest["MA60"]:
            score += 2
        if latest["MA20"] > latest["MA60"]:
            score += 2

        if 45 <= latest["RSI"] <= 65:
            score += 3
        elif 65 < latest["RSI"] <= 70:
            score += 1
        elif latest["RSI"] > 75:
            score -= 2
        elif latest["RSI"] < 30:
            score -= 1

        if return_1m > 5:
            score += 2
        elif return_1m > 0:
            score += 1

        if return_6m > 20:
            score += 2
        elif return_6m > 5:
            score += 1

        if volume_ratio > 1.5:
            score += 1

        if volatility > 4:
            score -= 1

        if latest["RSI"] > 75:
            category = "과열"
            action = "눌림목 대기"
        elif latest["Close"] < latest["MA60"]:
            category = "약세"
            action = "관망"
        elif score >= 8:
            category = "TOP 관심"
            action = "분할매수 후보"
        elif score >= 5:
            category = "관심"
            action = "추적관찰"
        else:
            category = "보류"
            action = "매수 보류"

        results.append({
            "종목": name,
            "티커": symbol,
            "현재가": round(latest["Close"], 2),
            "RSI": round(latest["RSI"], 2),
            "MA20": round(latest["MA20"], 2),
            "MA60": round(latest["MA60"], 2),
            "1개월수익률(%)": round(return_1m, 2),
            "6개월수익률(%)": round(return_6m, 2),
            "거래량비율": round(volume_ratio, 2),
            "변동성(%)": round(volatility, 2),
            "점수": score,
            "분류": category,
            "추천행동": action
        })

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data["Close"], label="Close")
        plt.plot(data.index, data["MA20"], label="MA20")
        plt.plot(data.index, data["MA60"], label="MA60")
        plt.title(f"{name} ({symbol})")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)

        filename = f"{symbol.replace('.', '_')}_{name}.png"
        plt.savefig(os.path.join(chart_dir, filename))
        plt.close()

    except Exception as e:
        print(f"{name} 오류: {e}")

df = pd.DataFrame(results)
df = df.sort_values(by="점수", ascending=False)

df.to_csv("auto_rank_result.csv", index=False, encoding="utf-8-sig")

print("\n===== 전체 관심 종목 자동 랭킹 =====")
print(df.to_string(index=False))

print("\n===== TOP 5 관심 종목 =====")
print(df.head(5).to_string(index=False))

print("\n===== 과열주의 종목 =====")
print(df[df["분류"] == "과열"].to_string(index=False))

print("\n===== 약세주의 종목 =====")
print(df[df["분류"] == "약세"].to_string(index=False))

print("\nCSV 저장 완료: auto_rank_result.csv")
print("차트 저장 완료: rank_charts 폴더")