import json
import os
import platform
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd


def _configure_matplotlib():
    import matplotlib.font_manager as fm

    if platform.system() == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"
    else:
        available = {f.name for f in fm.fontManager.ttflist}
        if "NanumGothic" in available:
            plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False


class ReportWriter:
    def __init__(self, output_dir: str = "output"):
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.latest_dir = os.path.join(output_dir, "latest")
        self.history_dir = os.path.join(output_dir, "history", date_str)
        self.latest_chart_dir = os.path.join(self.latest_dir, "charts")
        self.history_chart_dir = os.path.join(self.history_dir, "charts")

        for d in [self.latest_dir, self.history_dir, self.latest_chart_dir, self.history_chart_dir]:
            os.makedirs(d, exist_ok=True)

    def save(self, df: pd.DataFrame, raw_data: dict | None = None):
        self._save_csv(df)
        self._save_json(df)
        self._save_text_report(df)
        if raw_data:
            self._save_charts(df, raw_data)

    # ── CSV ──────────────────────────────────────────────────────────────────

    def _save_csv(self, df: pd.DataFrame):
        csv_df = df.drop(columns=["점수상세"], errors="ignore")
        for path in self._both("all_stock_rank.csv"):
            csv_df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"CSV  저장: {self._latest('all_stock_rank.csv')}")

    # ── JSON ─────────────────────────────────────────────────────────────────

    def _save_json(self, df: pd.DataFrame):
        payload = {
            "generated_at": datetime.now().isoformat(),
            "total": len(df),
            "stocks": df.to_dict(orient="records"),
        }
        for path in self._both("all_stock_rank.json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"JSON 저장: {self._latest('all_stock_rank.json')}")

    # ── Text report ───────────────────────────────────────────────────────────

    def _save_text_report(self, df: pd.DataFrame):
        lines = [
            "===== AI Trading Stock Report =====",
            f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"분석 종목 수: {len(df)}",
        ]
        for cat, label in [
            ("TOP 관심", "TOP 관심 종목"),
            ("매수후보", "매수후보 종목"),
            ("관망", "관망 종목"),
            ("과열", "과열 종목"),
            ("약세", "약세 종목"),
            ("위험", "위험 종목"),
        ]:
            sub = df[df["분류"] == cat]
            if sub.empty:
                continue
            lines.append(f"\n===== {label} ({len(sub)}개) =====")
            for _, row in sub.iterrows():
                lines.append(
                    f"  {row['종목']} ({row['티커']}) | 점수:{row['점수']} | RSI:{row['RSI']} | {row['추천행동']}"
                )

        text = "\n".join(lines)
        for path in self._both("daily_report.txt"):
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        print(f"리포트 저장: {self._latest('daily_report.txt')}")

    # ── Charts ────────────────────────────────────────────────────────────────

    def _save_charts(self, df: pd.DataFrame, raw_data: dict):
        _configure_matplotlib()

        for name, data in raw_data.items():
            match = df[df["종목"] == name]
            if match.empty:
                continue
            row = match.iloc[0]
            symbol = row["티커"]
            category = row["분류"]
            score = row["점수"]

            fig, axes = plt.subplots(
                3, 1, figsize=(14, 12),
                gridspec_kw={"height_ratios": [4, 2, 2]}
            )

            # — Price + MAs + Bollinger —
            ax = axes[0]
            ax.fill_between(data.index, data["BB_Upper"], data["BB_Lower"], alpha=0.08, color="gray")
            ax.plot(data.index, data["BB_Upper"], color="gray", linewidth=0.6, linestyle="--")
            ax.plot(data.index, data["BB_Lower"], color="gray", linewidth=0.6, linestyle="--")
            ax.plot(data.index, data["Close"], label="Close", linewidth=1.8, color="#1f77b4")
            ax.plot(data.index, data["MA20"], label="MA20", linewidth=1.1, color="orange")
            ax.plot(data.index, data["MA60"], label="MA60", linewidth=1.1, color="red")
            if "MA120" in data.columns:
                ax.plot(data.index, data["MA120"], label="MA120", linewidth=1.0, linestyle="--", color="purple")
            ax.set_title(f"{name} ({symbol})  —  {category}  |  점수: {score}")
            ax.legend(loc="upper left", fontsize=8)
            ax.grid(True, alpha=0.3)

            # — RSI —
            ax = axes[1]
            ax.plot(data.index, data["RSI"], color="purple", linewidth=1.2)
            ax.axhline(70, color="red", linestyle="--", alpha=0.6, linewidth=0.8)
            ax.axhline(30, color="green", linestyle="--", alpha=0.6, linewidth=0.8)
            ax.set_ylim(0, 100)
            ax.set_ylabel("RSI")
            ax.grid(True, alpha=0.3)

            # — MACD —
            ax = axes[2]
            colors = ["green" if v >= 0 else "red" for v in data["MACD_Hist"]]
            ax.bar(data.index, data["MACD_Hist"], color=colors, alpha=0.5, width=0.8)
            ax.plot(data.index, data["MACD"], label="MACD", linewidth=1.1)
            ax.plot(data.index, data["MACD_Signal"], label="Signal", linewidth=1.1, color="red")
            ax.axhline(0, color="black", linewidth=0.5)
            ax.set_ylabel("MACD")
            ax.legend(loc="upper left", fontsize=8)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            filename = f"{symbol.replace('.', '_')}_{name}.png"
            for chart_dir in [self.latest_chart_dir, self.history_chart_dir]:
                plt.savefig(os.path.join(chart_dir, filename), dpi=100, bbox_inches="tight")
            plt.close()

        print(f"차트 저장: {self.latest_chart_dir}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _latest(self, filename: str) -> str:
        return os.path.join(self.latest_dir, filename)

    def _both(self, filename: str) -> list[str]:
        return [
            os.path.join(self.latest_dir, filename),
            os.path.join(self.history_dir, filename),
        ]
