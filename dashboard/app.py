import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf

st.set_page_config(
    page_title="AI 주식 분석 대시보드",
    page_icon="📈",
    layout="wide",
)

JSON_PATH = Path("output/latest/all_stock_rank.json")
INDICES_PATH = Path("output/latest/market_indices.json")

CATEGORY_COLOR = {
    "TOP 관심": "#27ae60",
    "매수후보": "#2ecc71",
    "관망":    "#f39c12",
    "과열":    "#e67e22",
    "약세":    "#e74c3c",
    "위험":    "#c0392b",
}


# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_ranking() -> tuple[pd.DataFrame | None, str | None, bool]:
    if not JSON_PATH.exists():
        return None, None, False
    with open(JSON_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    stale = bool(raw.get("stale", False))
    return pd.DataFrame(raw["stocks"]), raw["generated_at"], stale


@st.cache_data(ttl=300)
def load_indices() -> dict:
    if not INDICES_PATH.exists():
        return {}
    with open(INDICES_PATH, encoding="utf-8") as f:
        return json.load(f).get("indices", {})


@st.cache_data(ttl=600)
def fetch_ohlcv(ticker: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period="6mo")


# ── Chart builders ────────────────────────────────────────────────────────────

def price_chart(data: pd.DataFrame, name: str, symbol: str) -> go.Figure:
    ma20 = data["Close"].rolling(20).mean()
    ma60 = data["Close"].rolling(60).mean()
    bb = ta.volatility.BollingerBands(data["Close"], window=20)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data.index, y=bb.bollinger_hband(), name="BB Upper",
        line=dict(color="lightgray", width=0.5), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=bb.bollinger_lband(), name="Bollinger Band",
        line=dict(color="lightgray", width=0.5),
        fill="tonexty", fillcolor="rgba(200,200,200,0.15)",
    ))
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Close",
                             line=dict(color="#1f77b4", width=2)))
    fig.add_trace(go.Scatter(x=data.index, y=ma20, name="MA20",
                             line=dict(color="orange", width=1.3)))
    fig.add_trace(go.Scatter(x=data.index, y=ma60, name="MA60",
                             line=dict(color="red", width=1.3)))
    if len(data) >= 120:
        ma120 = data["Close"].rolling(120).mean()
        fig.add_trace(go.Scatter(x=data.index, y=ma120, name="MA120",
                                 line=dict(color="purple", width=1.0, dash="dot")))
    fig.update_layout(
        title=f"{name}  ({symbol})",
        height=400,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def rsi_chart(data: pd.DataFrame) -> go.Figure:
    rsi = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=rsi, name="RSI",
                             line=dict(color="purple", width=1.5)))
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.05, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.05, line_width=0)
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수 70")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="과매도 30")
    fig.update_layout(title="RSI (14)", height=230,
                      yaxis=dict(range=[0, 100]), showlegend=False)
    return fig


def macd_chart(data: pd.DataFrame) -> go.Figure:
    ind = ta.trend.MACD(data["Close"])
    hist = ind.macd_diff()
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in hist]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data.index, y=hist, name="Histogram",
                         marker_color=colors, opacity=0.6))
    fig.add_trace(go.Scatter(x=data.index, y=ind.macd(), name="MACD",
                             line=dict(color="#1f77b4", width=1.3)))
    fig.add_trace(go.Scatter(x=data.index, y=ind.macd_signal(), name="Signal",
                             line=dict(color="red", width=1.3)))
    fig.update_layout(title="MACD", height=230,
                      legend=dict(orientation="h", y=-0.2))
    return fig


def score_breakdown_chart(breakdown: dict) -> go.Figure:
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colors = ["#2ecc71" if v > 0 else "#e74c3c" if v < 0 else "#95a5a6" for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors))
    fig.update_layout(title="점수 상세 분석", height=260, showlegend=False,
                      yaxis=dict(zeroline=True))
    return fig


def returns_chart(row) -> go.Figure:
    periods = ["1개월", "3개월", "6개월"]
    vals = [row.get("1개월수익률(%)", 0), row.get("3개월수익률(%)", 0), row.get("6개월수익률(%)", 0)]
    colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in vals]
    fig = go.Figure(go.Bar(x=periods, y=vals, marker_color=colors))
    fig.add_hline(y=0, line_color="black", line_width=0.8)
    fig.update_layout(title="기간별 수익률 (%)", height=260, showlegend=False)
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.title("📈 AI 주식 분석 대시보드")

    df, generated_at, is_stale = load_ranking()

    if df is None:
        st.warning("분석 결과가 없습니다. 아래 명령을 먼저 실행하세요.")
        st.code("python main.py\n# 또는\npython scheduler/morning_runner.py")
        st.stop()

    if is_stale:
        st.warning(f"⚠️ 마지막 분석 실행에 실패했습니다. 표시 데이터가 오래됐을 수 있습니다. (기준: {generated_at})")
    else:
        st.caption(f"마지막 업데이트: {generated_at}")

    # ── 시장 지수 패널 ────────────────────────────────────────────────────────
    indices = load_indices()
    if indices:
        idx_cols = st.columns(len(indices))
        for col, (name, data) in zip(idx_cols, indices.items()):
            delta_str = f"{data['change_pct']:+.2f}%"
            col.metric(name, f"{data['close']:,.2f}", delta_str)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("🔧 필터")
        market_opt = st.selectbox("시장", ["전체", "US", "KR"])
        all_cats = sorted(df["분류"].unique().tolist())
        cat_opt = st.multiselect("분류", all_cats, default=all_cats)
        st.divider()
        if st.button("🔄 데이터 새로고침"):
            st.cache_data.clear()
            st.rerun()

    # ── Filter ───────────────────────────────────────────────────────────────
    view = df.copy()
    if market_opt != "전체":
        view = view[view["시장"] == market_opt]
    if cat_opt:
        view = view[view["분류"].isin(cat_opt)]

    # ── Summary metrics ───────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("전체 종목", len(df))
    c2.metric("🟢 TOP 관심", len(df[df["분류"] == "TOP 관심"]))
    c3.metric("🟡 매수후보", len(df[df["분류"] == "매수후보"]))
    c4.metric("🔴 과열",     len(df[df["분류"] == "과열"]))
    c5.metric("⚫ 위험",     len(df[df["분류"] == "위험"]))

    st.divider()

    # ── Ranking table ─────────────────────────────────────────────────────────
    st.subheader("📊 전체 랭킹")

    display_cols = [
        "종목", "티커", "시장", "통화", "현재가", "RSI",
        "1개월수익률(%)", "3개월수익률(%)", "6개월수익률(%)",
        "거래량비율", "변동성(%)", "점수", "분류", "추천행동",
    ]
    cols = [c for c in display_cols if c in view.columns]

    def color_row(row):
        color = CATEGORY_COLOR.get(row["분류"], "")
        return [f"background-color: {color}22" if color else "" for _ in row]

    styled = view[cols].style.apply(color_row, axis=1)
    st.dataframe(styled, use_container_width=True, height=430)

    st.divider()

    # ── Individual stock ──────────────────────────────────────────────────────
    st.subheader("🔍 종목별 상세 분석")

    if view.empty:
        st.info("조건에 맞는 종목이 없습니다.")
        return

    selected = st.selectbox("종목 선택", view["종목"].tolist())
    row = view[view["종목"] == selected].iloc[0]
    ticker = row["티커"]
    currency = row["통화"]

    m1, m2, m3, m4, m5 = st.columns(5)
    price_fmt = (
        f"{row['현재가']:,.0f}" if currency == "KRW"
        else f"{row['현재가']:,.2f}"
    )
    m1.metric("현재가",   f"{currency} {price_fmt}")
    m2.metric("RSI",      f"{row['RSI']:.1f}")
    m3.metric("점수",     row["점수"])
    m4.metric("분류",     row["분류"])
    m5.metric("추천행동", row["추천행동"])

    ohlcv = fetch_ohlcv(ticker)
    if ohlcv.empty:
        st.error("차트 데이터를 불러올 수 없습니다.")
        return

    st.plotly_chart(price_chart(ohlcv, selected, ticker), use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(rsi_chart(ohlcv), use_container_width=True)
    with col_r:
        st.plotly_chart(macd_chart(ohlcv), use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        breakdown = row.get("점수상세")
        if isinstance(breakdown, dict) and breakdown:
            st.plotly_chart(score_breakdown_chart(breakdown), use_container_width=True)
    with col_r2:
        st.plotly_chart(returns_chart(row), use_container_width=True)


if __name__ == "__main__":
    main()
