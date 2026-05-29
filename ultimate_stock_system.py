import os
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
from datetime import datetime

# =========================
# 종목 리스트
# =========================

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

# =========================
# 폴더 생성
# =========================

base_dir = "stock_output"
chart_dir = os.path.join(base_dir, "charts")
report_dir = os.path.join(base_dir, "reports")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(chart_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

results = []

# =========================
# 분석 시작
# =========================

for name, symbol in stocks.items():

    try:
        print(f"분석 중: {name}")

        data = yf.Ticker(symbol).history(period="6mo")

        if data.empty or len(data) < 60:
            print(f"데이터 부족: {name}")
            continue

        # =========================
        # 기술 지표
        # =========================

        data["RSI"] = ta.momentum.RSIIndicator(
            data["Close"],
            window=14
        ).rsi()

        data["MA20"] = data["Close"].rolling(20).mean()
        data["MA60"] = data["Close"].rolling(60).mean()

        data["Volume_MA20"] = data["Volume"].rolling(20).mean()

        latest = data.iloc[-1]
        start = data.iloc[0]

        current_price = latest["Close"]
        rsi = latest["RSI"]
        ma20 = latest["MA20"]
        ma60 = latest["MA60"]

        return_1m = (
            (current_price - data.iloc[-20]["Close"])
            / data.iloc[-20]["Close"]
        ) * 100

        return_6m = (
            (current_price - start["Close"])
            / start["Close"]
        ) * 100

        volume_ratio = latest["Volume"] / latest["Volume_MA20"]

        volatility = data["Close"].pct_change().std() * 100

        # =========================
        # 점수 계산
        # =========================

        score = 0

        # 추세
        if current_price > ma20:
            score += 2

        if current_price > ma60:
            score += 2

        if ma20 > ma60:
            score += 2

        # RSI
        if 45 <= rsi <= 65:
            score += 3
        elif 65 < rsi <= 70:
            score += 1
        elif rsi >= 70:
            score -= 2
        elif rsi < 30:
            score -= 1

        # 1개월 수익률
        if return_1m > 15:
            score += 3
        elif return_1m > 5:
            score += 2
        elif return_1m > 0:
            score += 1

        # 6개월 수익률
        if return_6m > 50:
            score += 3
        elif return_6m > 20:
            score += 2
        elif return_6m > 5:
            score += 1

        # 거래량 증가
        if volume_ratio > 2:
            score += 2
        elif volume_ratio > 1.5:
            score += 1

        # 변동성 과도
        if volatility > 5:
            score -= 2
        elif volatility > 4:
            score -= 1

        # =========================
        # 최종 분류
        # =========================

        if rsi >= 75:
            category = "과열"
            action = "눌림목 대기"

        elif current_price < ma60:
            category = "약세"
            action = "관망"

        elif score >= 10:
            category = "TOP 관심"
            action = "분할매수 후보"

        elif score >= 7:
            category = "관심"
            action = "추적관찰"

        else:
            category = "보류"
            action = "매수 보류"

        # =========================
        # 결과 저장
        # =========================

        results.append({
            "종목": name,
            "티커": symbol,
            "현재가": round(current_price, 2),
            "RSI": round(rsi, 2),
            "MA20": round(ma20, 2),
            "MA60": round(ma60, 2),
            "1개월수익률(%)": round(return_1m, 2),
            "6개월수익률(%)": round(return_6m, 2),
            "거래량비율": round(volume_ratio, 2),
            "변동성(%)": round(volatility, 2),
            "점수": score,
            "분류": category,
            "추천행동": action
        })

        # =========================
        # 차트 생성
        # =========================

        plt.figure(figsize=(14, 7))

        plt.plot(data.index, data["Close"], label="Close")
        plt.plot(data.index, data["MA20"], label="MA20")
        plt.plot(data.index, data["MA60"], label="MA60")

        plt.title(f"{name} ({symbol})")
        plt.xlabel("Date")
        plt.ylabel("Price")

        plt.legend()
        plt.grid(True)

        filename = f"{symbol.replace('.', '_')}_{name}.png"

        chart_path = os.path.join(chart_dir, filename)

        plt.savefig(chart_path)
        plt.close()

    except Exception as e:
        print(f"오류 발생: {name} / {e}")

# =========================
# DataFrame 생성
# =========================

if len(results) == 0:
    print("분석 결과 없음")
    exit()


df = pd.DataFrame(results)

# 점수순 정렬

df = df.sort_values(by="점수", ascending=False)

# =========================
# CSV 저장
# =========================

all_csv = os.path.join(base_dir, "all_stock_rank.csv")

df.to_csv(all_csv, index=False, encoding="utf-8-sig")

# TOP 관심 종목 저장

top_df = df[df["분류"] == "TOP 관심"]

top_csv = os.path.join(base_dir, "top_interest_stocks.csv")

top_df.to_csv(top_csv, index=False, encoding="utf-8-sig")

# =========================
# 리포트 생성
# =========================

report_lines = []

report_lines.append("===== Sung AI Stock Report =====\n")
report_lines.append(f"생성 시간: {datetime.now()}\n")

report_lines.append("\n===== TOP 관심 종목 =====\n")

for _, row in top_df.iterrows():
    report_lines.append(
        f"{row['종목']} | 점수:{row['점수']} | RSI:{row['RSI']} | 행동:{row['추천행동']}"
    )

report_lines.append("\n===== 과열 종목 =====\n")

hot_df = df[df["분류"] == "과열"]

for _, row in hot_df.iterrows():
    report_lines.append(
        f"{row['종목']} | RSI:{row['RSI']} | 행동:{row['추천행동']}"
    )

report_lines.append("\n===== 약세 종목 =====\n")

weak_df = df[df["분류"] == "약세"]

for _, row in weak_df.iterrows():
    report_lines.append(
        f"{row['종목']} | 점수:{row['점수']} | 행동:{row['추천행동']}"
    )

report_text = "\n".join(report_lines)

report_file = os.path.join(report_dir, "daily_report.txt")

with open(report_file, "w", encoding="utf-8") as f:
    f.write(report_text)

# =========================
# 출력
# =========================

print("\n===== 전체 관심 종목 자동 랭킹 =====")
print(df.to_string(index=False))

print("\n===== TOP 관심 종목 =====")
print(top_df.to_string(index=False))

print("\n===== 과열 종목 =====")
print(hot_df.to_string(index=False))

print("\n===== 약세 종목 =====")
print(weak_df.to_string(index=False))

print("\n===== 저장 완료 =====")
print(f"전체 CSV: {all_csv}")
print(f"TOP 관심 CSV: {top_csv}")
print(f"리포트: {report_file}")
print(f"차트 폴더: {chart_dir}")