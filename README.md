# AI_TRADING

한국(.KS) 및 미국 주식의 기술적 분석과 랭킹을 자동화하는 Python 기반 시스템입니다.
yfinance로 OHLCV 데이터를 수집하고 RSI, MA20, MA60 등 기술 지표를 계산해 다중 팩터 점수로 종목을 평가합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

| 스크립트 | 설명 |
|---|---|
| `ultimate_stock_system.py` | 전체 파이프라인 — 14개 종목, CSV + 차트 + 텍스트 리포트 |
| `auto_rank_stocks.py` | 14개 종목, CSV + 차트 |
| `compare_stocks.py` | 8개 종목, 간소화 스코어링 |
| `multi_stock.py` | 미국 5개 종목, BUY/HOLD/CAUTION/SELL |
| `korea_stock.py` | 한국 2개 종목, 이진 신호 |

```bash
python ultimate_stock_system.py
```

## 출력 결과

| 스크립트 | CSV | 차트 | 리포트 |
|---|---|---|---|
| ultimate_stock_system.py | `stock_output/all_stock_rank.csv`, `stock_output/top_interest_stocks.csv` | `stock_output/charts/` | `stock_output/reports/daily_report.txt` |
| auto_rank_stocks.py | `auto_rank_result.csv` | `rank_charts/` | — |
| compare_stocks.py | `stock_compare_result.csv` | `charts/` | — |

## 스코어링 기준 (ultimate_stock_system.py)

| 팩터 | 조건 | 점수 |
|---|---|---|
| 추세 | 종가 > MA20 | +2 |
| | 종가 > MA60 | +2 |
| | MA20 > MA60 (골든크로스 구간) | +2 |
| RSI | 45–65 | +3 |
| | 65–70 | +1 |
| | ≥70 | −2 |
| | <30 | −1 |
| 1개월 수익률 | >15% / >5% / >0% | +3 / +2 / +1 |
| 6개월 수익률 | >50% / >20% / >5% | +3 / +2 / +1 |
| 거래량 비율 | >2.0 / >1.5 | +2 / +1 |
| 변동성 | >5% / >4% | −2 / −1 |

### 분류 기준

| 조건 | 분류 |
|---|---|
| RSI ≥ 75 | 과열 (눌림목 대기) |
| 종가 < MA60 | 약세 (관망) |
| 점수 ≥ 10 | TOP 관심 (분할매수 후보) |
| 점수 ≥ 7 | 관심 (추적관찰) |
| 그 외 | 보류 |

## 종목 추가

각 스크립트의 `stocks` 딕셔너리를 수정합니다.

```python
"LG에너지솔루션": "373220.KS"   # 한국: KRX 티커 + .KS
"Palantir": "PLTR"               # 미국: NYSE/NASDAQ 심볼
```
