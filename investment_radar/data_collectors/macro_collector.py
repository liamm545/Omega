from datetime import date

import pandas as pd
import requests

from utils.retry import retry_on_exception


@retry_on_exception()
def collect_macro_series(series_code: str, start_date: str, end_date: str):
    """TODO: connect ECOS/FRED. Returns empty frame until exact series/API is configured."""
    return pd.DataFrame(columns=["date", "series_code", "value", "source"])


YAHOO_MACRO_SYMBOLS = {
    "USD_KRW": {"symbol": "KRW=X", "name": "USD/KRW", "unit": "KRW"},
    "KOSPI": {"symbol": "^KS11", "name": "KOSPI", "unit": "pt"},
    "KOSDAQ": {"symbol": "^KQ11", "name": "KOSDAQ", "unit": "pt"},
    "SP500": {"symbol": "^GSPC", "name": "S&P500", "unit": "pt"},
    "NASDAQ": {"symbol": "^IXIC", "name": "NASDAQ", "unit": "pt"},
    "US10Y": {"symbol": "^TNX", "name": "미국 10년물", "unit": "%"},
    "WTI": {"symbol": "CL=F", "name": "WTI", "unit": "USD/bbl"},
    "NATGAS": {"symbol": "NG=F", "name": "천연가스", "unit": "USD/MMBtu"},
    "GOLD": {"symbol": "GC=F", "name": "금", "unit": "USD/oz"},
    "SILVER": {"symbol": "SI=F", "name": "은", "unit": "USD/oz"},
    "COPPER": {"symbol": "HG=F", "name": "구리", "unit": "USD/lb"},
    "SOX": {"symbol": "^SOX", "name": "필라델피아 반도체지수", "unit": "pt"},
}


def collect_yahoo_macro_indicators(timeout: int = 10) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    failures = []
    for indicator, config in YAHOO_MACRO_SYMBOLS.items():
        try:
            item = _fetch_yahoo_chart(config["symbol"], timeout=timeout)
        except requests.RequestException as error:
            failures.append(f"{indicator}/{config['symbol']}: {error}")
            continue
        if not item:
            failures.append(f"{indicator}/{config['symbol']}: empty response")
            continue
        rows.append(
            {
                "date": item["date"],
                "indicator": indicator,
                "name": config["name"],
                "value": item["value"],
                "unit": config["unit"],
                "change_1d": item["change_1d"],
                "change_1m": item["change_1m"],
                "source": f"Yahoo Finance:{config['symbol']}",
            }
        )
    return pd.DataFrame(rows, columns=_macro_columns()), failures


def collect_pykrx_market_indicators() -> tuple[pd.DataFrame, list[str]]:
    failures = []
    try:
        from pykrx import stock

        today = date.today().strftime("%Y%m%d")
        rows = []
        for index_ticker, indicator, name in [("1001", "KOSPI", "KOSPI"), ("2001", "KOSDAQ", "KOSDAQ")]:
            frame = stock.get_index_ohlcv_by_date("20250101", today, index_ticker).reset_index()
            if frame.empty:
                failures.append(f"{indicator}/{index_ticker}: empty response")
                continue
            frame = frame.rename(columns={"날짜": "date", "종가": "close"})
            frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
            frame = frame.sort_values("date")
            close = frame["close"].astype(float)
            rows.append(
                {
                    "date": frame.iloc[-1]["date"],
                    "indicator": indicator,
                    "name": name,
                    "value": float(close.iloc[-1]),
                    "unit": "pt",
                    "change_1d": _pct_change(close, 1),
                    "change_1m": _pct_change(close, 21),
                    "source": "pykrx",
                }
            )
        return pd.DataFrame(rows, columns=_macro_columns()), failures
    except Exception as error:
        return pd.DataFrame(columns=_macro_columns()), [f"pykrx indexes: {error}"]


def collect_macro_indicators() -> pd.DataFrame:
    macro, _ = collect_macro_indicators_with_diagnostics()
    return macro


def collect_macro_indicators_with_diagnostics() -> tuple[pd.DataFrame, list[str]]:
    yahoo, yahoo_failures = collect_yahoo_macro_indicators()
    krx, krx_failures = collect_pykrx_market_indicators()
    frames = [frame for frame in [yahoo, krx] if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=_macro_columns()), yahoo_failures + krx_failures
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=_macro_columns()), yahoo_failures + krx_failures
    return combined.drop_duplicates(subset=["date", "indicator"], keep="last"), yahoo_failures + krx_failures


def _fetch_yahoo_chart(symbol: str, timeout: int) -> dict:
    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "2mo", "interval": "1d"},
        timeout=timeout,
        headers={"User-Agent": "investment-radar/0.1"},
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("chart", {}).get("result", [])
    if not result:
        return {}
    result = result[0]
    timestamps = result.get("timestamp", [])
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    frame = pd.DataFrame({"timestamp": timestamps, "close": closes}).dropna()
    if frame.empty:
        return {}
    frame["date"] = pd.to_datetime(frame["timestamp"], unit="s").dt.strftime("%Y-%m-%d")
    close = frame["close"].astype(float)
    return {
        "date": frame.iloc[-1]["date"],
        "value": float(close.iloc[-1]),
        "change_1d": _pct_change(close, 1),
        "change_1m": _pct_change(close, 21),
    }


def _pct_change(series: pd.Series, periods: int):
    if len(series) <= periods:
        return None
    base = series.iloc[-periods - 1]
    if base == 0:
        return None
    return float((series.iloc[-1] / base - 1) * 100)


def _macro_columns() -> list[str]:
    return ["date", "indicator", "name", "value", "unit", "change_1d", "change_1m", "source"]
