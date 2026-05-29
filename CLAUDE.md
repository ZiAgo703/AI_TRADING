# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI_TRADING is a Python-based stock analysis and ranking system for Korean (.KS) and US equities. It fetches OHLCV data via yfinance, calculates technical indicators (RSI, MA20, MA60), applies a multi-factor scoring algorithm, and outputs ranked CSV reports, price charts, and text summaries.

## Running Scripts

All scripts are standalone — run any directly:

```bash
python ultimate_stock_system.py   # Full pipeline: 14 stocks, CSV + charts + text report
python auto_rank_stocks.py        # Same stocks, CSV + charts only, lower score thresholds
python compare_stocks.py          # 8 mixed stocks, simplified scoring
python multi_stock.py             # US only (5 stocks), binary BUY/HOLD/CAUTION/SELL
python korea_stock.py             # Korean only (2 stocks), binary signals
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Output Locations

| Script | CSV | Charts | Report |
|---|---|---|---|
| ultimate_stock_system.py | `stock_output/all_stock_rank.csv`, `stock_output/top_interest_stocks.csv` | `stock_output/charts/` | `stock_output/reports/daily_report.txt` |
| auto_rank_stocks.py | `auto_rank_result.csv` | `rank_charts/` | — |
| compare_stocks.py | `stock_compare_result.csv` | `charts/` | — |

## Architecture

### Data Pipeline (all scripts follow this pattern)
1. Define `stocks` dict: `{"표시명": "TICKER"}` — Korean stocks use `.KS` suffix
2. Fetch 3–6 months of OHLCV history via `yf.Ticker(symbol).history(period="6mo")`
3. Skip if `data.empty or len(data) < 60`
4. Calculate indicators: RSI(14), MA20, MA60, Volume_MA20
5. Score → categorize → append to `results`
6. Build DataFrame, sort by score, write CSV + charts

### Scoring System (ultimate_stock_system.py — the canonical version)

| Factor | Condition | Points |
|---|---|---|
| Trend | Close > MA20 | +2 |
| | Close > MA60 | +2 |
| | MA20 > MA60 (golden cross zone) | +2 |
| RSI | 45–65 | +3 |
| | 65–70 | +1 |
| | ≥70 | −2 |
| | <30 | −1 |
| 1-month return | >15% | +3 / >5% | +2 / >0% | +1 |
| 6-month return | >50% | +3 / >20% | +2 / >5% | +1 |
| Volume ratio | >2.0 | +2 / >1.5 | +1 |
| Volatility | >5% | −2 / >4% | −1 |

### Category Logic (ultimate_stock_system.py)

Priority order — first match wins:
1. RSI ≥ 75 → **과열** (눌림목 대기)
2. Close < MA60 → **약세** (관망)
3. Score ≥ 10 → **TOP 관심** (분할매수 후보)
4. Score ≥ 7 → **관심** (추적관찰)
5. else → **보류** (매수 보류)

### Script Differences

| Script | Stocks | Period | Score threshold (TOP) | 1m return | Vol bonus | Extra output |
|---|---|---|---|---|---|---|
| ultimate_stock_system.py | 14 (KR+US) | 6mo | ≥10 | Yes | Yes | text report |
| auto_rank_stocks.py | 14 (KR+US) | 6mo | ≥8 | Simplified | Simplified | — |
| compare_stocks.py | 8 (KR+US) | 6mo | ≥6 ("관심강함") | No | No | — |
| multi_stock.py | 5 (US) | 3mo | BUY/HOLD only | No | No | — |
| korea_stock.py | 2 (KR) | 3mo | BUY/HOLD only | No | No | — |

## CSV Column Reference

`all_stock_rank.csv` / `auto_rank_result.csv`:
```
종목, 티커, 현재가, RSI, MA20, MA60, 1개월수익률(%), 6개월수익률(%), 거래량비율, 변동성(%), 점수, 분류, 추천행동
```

`stock_compare_result.csv` (compare_stocks.py):
```
종목, 티커, 현재가, RSI, MA20, MA60, 6개월수익률(%), 변동성(%), 점수, 판단, 추천행동
```
Note: column name is `판단` not `분류`, and uses different signal names (`관심강함`, `과열주의`, `약세주의`).

## Adding Stocks

Edit the `stocks` dict in the target script:
```python
"LG에너지솔루션": "373220.KS"   # Korean: name -> KRX ticker + .KS
"Palantir": "PLTR"               # US: name -> NYSE/NASDAQ symbol
```

## Known Gaps (for future improvement)

- `requirements.txt` exists (yfinance, pandas, numpy, matplotlib, ta, requests)
- No shared module — scoring logic is duplicated across every script
- Inconsistent scoring weights and thresholds between scripts
- No MACD, Bollinger Bands, or volume-weighted indicators
- No backtesting framework
- No scheduling/automation (runs manually only)
- Chart filenames use Korean characters which may cause encoding issues on some systems
