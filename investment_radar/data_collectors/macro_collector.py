from datetime import date
from io import StringIO

import pandas as pd
import requests

from utils.retry import retry_on_exception
from utils.env import get_env


@retry_on_exception()
def collect_macro_series(series_code: str, start_date: str, end_date: str):
    """TODO: connect ECOS/FRED. Returns empty frame until exact series/API is configured."""
    return pd.DataFrame(columns=["date", "series_code", "value", "source"])


FRED_MACRO_SERIES = {
    "SP500": {"series": "SP500", "name": "S&P500", "unit": "pt"},
    "NASDAQ": {"series": "NASDAQCOM", "name": "NASDAQ", "unit": "pt"},
    "US10Y": {"series": "DGS10", "name": "미국 10년물", "unit": "%"},
    "WTI": {"series": "DCOILWTICO", "name": "WTI", "unit": "USD/bbl"},
    "NATGAS": {"series": "DHHNGSP", "name": "천연가스", "unit": "USD/MMBtu"},
    "COPPER": {"series": "PCOPPUSDM", "name": "구리", "unit": "USD/metric ton"},
    "SOX": {"series": "NASDAQSOX", "name": "필라델피아 반도체지수", "unit": "pt"},
}

STOOQ_QUOTE_SYMBOLS = {
    "SP500": {"symbol": "^spx", "name": "S&P500", "unit": "pt"},
    "NASDAQ": {"symbol": "^ndq", "name": "NASDAQ", "unit": "pt"},
    "WTI": {"symbol": "cl.f", "name": "WTI", "unit": "USD/bbl"},
    "NATGAS": {"symbol": "ng.f", "name": "천연가스", "unit": "USD/MMBtu"},
    "COPPER": {"symbol": "hg.f", "name": "구리", "unit": "USD/lb"},
    "SOX": {"symbol": "soxx.us", "name": "필라델피아 반도체지수 대체(SOXX)", "unit": "USD"},
    "GOLD": {"symbol": "gc.f", "name": "금", "unit": "USD/oz"},
    "SILVER": {"symbol": "xagusd", "name": "은", "unit": "USD/oz"},
}

NAVER_INDEX_CODES = {
    "KOSPI": {"code": "KOSPI", "name": "KOSPI", "unit": "pt"},
    "KOSDAQ": {"code": "KOSDAQ", "name": "KOSDAQ", "unit": "pt"},
}


def collect_fred_macro_indicators(timeout: int = 10) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    failures = []
    for indicator, config in FRED_MACRO_SERIES.items():
        try:
            item = _fetch_fred_series(config["series"], timeout=timeout)
        except requests.RequestException as error:
            failures.append(f"{indicator}/{config['series']}: {error}")
            continue
        if not item:
            failures.append(f"{indicator}/{config['series']}: empty response")
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
                "source": f"FRED:{config['series']}",
            }
        )
    return pd.DataFrame(rows, columns=_macro_columns()), failures


def collect_fx_indicators(timeout: int = 10) -> tuple[pd.DataFrame, list[str]]:
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": "USD", "to": "KRW"},
            timeout=timeout,
            headers={"User-Agent": "investment-radar/0.1"},
        )
        response.raise_for_status()
        payload = response.json()
        value = payload.get("rates", {}).get("KRW")
        if value is None:
            return pd.DataFrame(columns=_macro_columns()), ["USD_KRW/Frankfurter: KRW missing"]
        row = {
            "date": payload.get("date") or date.today().isoformat(),
            "indicator": "USD_KRW",
            "name": "USD/KRW",
            "value": float(value),
            "unit": "KRW",
            "change_1d": None,
            "change_1m": None,
            "source": "Frankfurter:USD/KRW",
        }
        return pd.DataFrame([row], columns=_macro_columns()), []
    except requests.RequestException as error:
        return pd.DataFrame(columns=_macro_columns()), [f"USD_KRW/Frankfurter: {error}"]


def collect_stooq_quote_indicators(timeout: int = 10) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    failures = []
    for indicator, config in STOOQ_QUOTE_SYMBOLS.items():
        try:
            response = requests.get(
                "https://stooq.com/q/l/",
                params={"s": config["symbol"], "f": "sd2t2ohlcv", "h": "", "e": "csv"},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 investment-radar/0.1"},
            )
            response.raise_for_status()
            frame = pd.read_csv(StringIO(response.text))
            if frame.empty or frame.iloc[0].get("Close") in (None, "N/D"):
                failures.append(f"{indicator}/{config['symbol']}: empty response")
                continue
            close = float(frame.iloc[0]["Close"])
            open_value = pd.to_numeric(frame.iloc[0].get("Open"), errors="coerce")
            change_1d = float((close / open_value - 1) * 100) if pd.notna(open_value) and open_value else None
            rows.append(
                {
                    "date": frame.iloc[0].get("Date") or date.today().isoformat(),
                    "indicator": indicator,
                    "name": config["name"],
                    "value": close,
                    "unit": config["unit"],
                    "change_1d": change_1d,
                    "change_1m": None,
                    "source": f"Stooq:{config['symbol']}",
                }
            )
        except (requests.RequestException, ValueError) as error:
            failures.append(f"{indicator}/{config['symbol']}: {error}")
    return pd.DataFrame(rows, columns=_macro_columns()), failures


def collect_naver_market_indices(timeout: int = 10) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    failures = []
    for indicator, config in NAVER_INDEX_CODES.items():
        try:
            response = requests.get(
                f"https://m.stock.naver.com/api/index/{config['code']}/price",
                params={"pageSize": 30, "page": 1},
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 investment-radar/0.1",
                    "Referer": "https://m.stock.naver.com/",
                },
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                failures.append(f"{indicator}/NaverStock: empty response")
                continue
            latest = payload[0]
            close = _parse_number(latest.get("closePrice"))
            if close is None:
                failures.append(f"{indicator}/NaverStock: closePrice missing")
                continue
            rows.append(
                {
                    "date": latest.get("localTradedAt") or date.today().isoformat(),
                    "indicator": indicator,
                    "name": config["name"],
                    "value": close,
                    "unit": config["unit"],
                    "change_1d": _parse_number(latest.get("fluctuationsRatio")),
                    "change_1m": _pct_change(pd.Series([_parse_number(item.get("closePrice")) for item in reversed(payload)]).dropna(), 21),
                    "source": f"NAVER_STOCK_INDEX:{config['code']}",
                }
            )
        except (requests.RequestException, ValueError, TypeError) as error:
            failures.append(f"{indicator}/NaverStock: {error}")
    return pd.DataFrame(rows, columns=_macro_columns()), failures


def collect_pykrx_market_indicators() -> tuple[pd.DataFrame, list[str]]:
    try:
        from pykrx import stock

        today = date.today().strftime("%Y%m%d")
        rows = []
        for index_ticker, indicator, name in [("1001", "KOSPI", "KOSPI"), ("2001", "KOSDAQ", "KOSDAQ")]:
            frame = stock.get_index_ohlcv_by_date("20250101", today, index_ticker).reset_index()
            if frame.empty:
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
        return pd.DataFrame(rows, columns=_macro_columns()), []
    except Exception:
        return pd.DataFrame(columns=_macro_columns()), []


def collect_macro_indicators() -> pd.DataFrame:
    macro, _ = collect_macro_indicators_with_diagnostics()
    return macro


def collect_macro_indicators_with_diagnostics() -> tuple[pd.DataFrame, list[str]]:
    fx, fx_failures = collect_fx_indicators()
    fred, fred_failures = collect_fred_macro_indicators()
    stooq, stooq_failures = collect_stooq_quote_indicators()
    naver_indexes, naver_index_failures = collect_naver_market_indices()
    if get_env("ENABLE_PYKRX_INDEXES", "false").lower() == "true":
        krx, krx_failures = collect_pykrx_market_indicators()
    else:
        krx, krx_failures = pd.DataFrame(columns=_macro_columns()), []
    frames = [
        frame.dropna(axis=1, how="all")
        for frame in [fx, fred, stooq, naver_indexes, krx]
        if not frame.empty
    ]
    if not frames:
        return pd.DataFrame(columns=_macro_columns()), fx_failures + fred_failures + stooq_failures + naver_index_failures + krx_failures
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=_macro_columns()), fx_failures + fred_failures + stooq_failures + naver_index_failures + krx_failures
    combined["priority"] = combined["source"].apply(_source_priority)
    combined = combined.sort_values(["indicator", "priority"]).drop_duplicates(subset=["indicator"], keep="first")
    return combined.drop(columns=["priority"], errors="ignore"), fx_failures + fred_failures + stooq_failures + naver_index_failures + krx_failures


def _fetch_fred_series(series_id: str, timeout: int) -> dict:
    response = requests.get(
        "https://fred.stlouisfed.org/graph/fredgraph.csv",
        params={"id": series_id},
        timeout=timeout,
        headers={"User-Agent": "investment-radar/0.1"},
    )
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    if frame.empty or series_id not in frame.columns:
        return {}
    frame = frame.rename(columns={"observation_date": "date", series_id: "value"})
    frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
    frame = frame.dropna(subset=["value"])
    if frame.empty:
        return {}
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    values = frame["value"].astype(float)
    return {
        "date": frame.iloc[-1]["date"],
        "value": float(values.iloc[-1]),
        "change_1d": _pct_change(values, 1),
        "change_1m": _pct_change(values, 21),
    }


def _pct_change(series: pd.Series, periods: int):
    if len(series) <= periods:
        return None
    base = series.iloc[-periods - 1]
    if base == 0:
        return None
    return float((series.iloc[-1] / base - 1) * 100)


def _parse_number(value):
    if value is None:
        return None
    number = pd.to_numeric(str(value).replace(",", ""), errors="coerce")
    if pd.isna(number):
        return None
    return float(number)


def _source_priority(source: str) -> int:
    source = source or ""
    if source.startswith("NAVER_STOCK_INDEX"):
        return 0
    if source.startswith("Frankfurter"):
        return 0
    if source.startswith("FRED"):
        return 1
    if source.startswith("Stooq"):
        return 2
    return 9


def _macro_columns() -> list[str]:
    return ["date", "indicator", "name", "value", "unit", "change_1d", "change_1m", "source"]
