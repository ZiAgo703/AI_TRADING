import math


def _safe(val) -> float | None:
    try:
        v = float(val)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def score_stock(latest, returns: dict) -> dict:
    """
    Score breakdown (max ~24 points):
      추세        : +7  (MA20/MA60/MA120 돌파 + 골든크로스)
      RSI         : +3 / -2
      MACD        : +2
      볼린저밴드  : +2
      1개월수익률 : +3
      3개월수익률 : +2
      6개월수익률 : +3
      거래량      : +2
      변동성      : -2
    """
    score = 0
    breakdown = {}

    close = _safe(latest["Close"])
    rsi = _safe(latest["RSI"])
    ma20 = _safe(latest["MA20"])
    ma60 = _safe(latest["MA60"])
    ma120 = _safe(latest["MA120"])
    macd = _safe(latest["MACD"])
    macd_sig = _safe(latest["MACD_Signal"])
    bb_middle = _safe(latest["BB_Middle"])
    bb_lower = _safe(latest["BB_Lower"])
    volume = _safe(latest["Volume"])
    vol_ma20 = _safe(latest["Volume_MA20"])
    volume_ratio = (volume / vol_ma20) if (vol_ma20 and vol_ma20 > 0) else 1.0

    # 추세 (max +7)
    s = 0
    if close and ma20 and close > ma20:
        s += 2
    if close and ma60 and close > ma60:
        s += 2
    if close and ma120 and close > ma120:
        s += 1
    if ma20 and ma60 and ma20 > ma60:
        s += 2
    score += s
    breakdown["추세"] = s

    # RSI (max +3, min -2)
    s = 0
    if rsi is not None:
        if 40 <= rsi <= 60:
            s = 3
        elif 60 < rsi <= 70:
            s = 1
        elif rsi >= 75:
            s = -2
        elif rsi < 30:
            s = -1
    score += s
    breakdown["RSI"] = s

    # MACD (max +2)
    s = 2 if (macd is not None and macd_sig is not None and macd > macd_sig) else 0
    score += s
    breakdown["MACD"] = s

    # 볼린저밴드 (max +2)
    s = 0
    if close and bb_middle and close > bb_middle:
        s += 1
    if close and bb_lower and close <= bb_lower * 1.02:
        s += 1
    score += s
    breakdown["볼린저밴드"] = s

    # 1개월 수익률 (max +3)
    s = 3 if returns["1m"] > 15 else 2 if returns["1m"] > 5 else 1 if returns["1m"] > 0 else 0
    score += s
    breakdown["1개월수익률"] = s

    # 3개월 수익률 (max +2)
    s = 2 if returns["3m"] > 20 else 1 if returns["3m"] > 5 else 0
    score += s
    breakdown["3개월수익률"] = s

    # 6개월 수익률 (max +3)
    s = 3 if returns["6m"] > 50 else 2 if returns["6m"] > 20 else 1 if returns["6m"] > 5 else 0
    score += s
    breakdown["6개월수익률"] = s

    # 거래량 (max +2)
    s = 2 if volume_ratio > 2.0 else 1 if volume_ratio > 1.5 else 0
    score += s
    breakdown["거래량"] = s

    # 변동성 패널티 (min -2)
    s = -2 if returns["volatility"] > 5 else -1 if returns["volatility"] > 4 else 0
    score += s
    breakdown["변동성"] = s

    return {"score": score, "breakdown": breakdown, "volume_ratio": volume_ratio}


def classify_stock(latest, score: int) -> tuple[str, str]:
    rsi = _safe(latest["RSI"])
    close = _safe(latest["Close"])
    ma60 = _safe(latest["MA60"])

    if rsi and rsi >= 75:
        return "과열", "눌림목 대기"
    if close and ma60 and close < ma60:
        return "약세", "관망"
    if score >= 12:
        return "TOP 관심", "분할매수 후보"
    if score >= 8:
        return "매수후보", "소량매수 검토"
    if score >= 4:
        return "관망", "추적관찰"
    return "위험", "매수 금지"
