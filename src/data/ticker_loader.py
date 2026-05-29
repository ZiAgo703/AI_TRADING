import json
from pathlib import Path


def load_tickers(config_dir: str = "configs") -> dict:
    """Returns {name: {ticker, market, currency}}"""
    tickers = {}
    sources = [
        ("tickers_us.json", "US", "USD"),
        ("tickers_kr.json", "KR", "KRW"),
    ]
    for filename, market, currency in sources:
        path = Path(config_dir) / filename
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        for item in items:
            tickers[item["name"]] = {
                "ticker": item["ticker"],
                "market": market,
                "currency": currency,
            }
    return tickers
