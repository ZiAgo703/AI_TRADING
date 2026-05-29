from datetime import datetime

from src.analysis.stock_analyzer import StockAnalyzer
from src.report.report_writer import ReportWriter


def main():
    print(f"\n{'=' * 52}")
    print(f"  AI 주식 분석 시작  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 52}\n")

    analyzer = StockAnalyzer(config_dir="configs")
    df, raw_data = analyzer.run()

    if df.empty:
        print("분석 결과 없음 — 네트워크 또는 데이터 문제를 확인하세요.")
        return

    print(f"\n분석 완료: {len(df)}개 종목\n")

    writer = ReportWriter(output_dir="output")
    writer.save(df, raw_data)

    print(f"\n{'=' * 52}")
    for cat, label in [
        ("TOP 관심", "🟢 TOP 관심"),
        ("매수후보", "🟡 매수후보"),
        ("과열",    "🔴 과열"),
        ("위험",    "⚫ 위험"),
    ]:
        sub = df[df["분류"] == cat]
        if sub.empty:
            continue
        print(f"\n===== {label} ({len(sub)}개) =====")
        for _, row in sub.iterrows():
            print(
                f"  {row['종목']:<16} ({row['티커']:<12}) | "
                f"점수:{row['점수']:>3} | RSI:{row['RSI']:>5.1f} | {row['추천행동']}"
            )

    print(f"\n완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 52}\n")


if __name__ == "__main__":
    main()
