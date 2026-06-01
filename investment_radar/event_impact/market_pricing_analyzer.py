from __future__ import annotations

from datetime import datetime

import pandas as pd


def analyze_market_pricing(prices: pd.DataFrame, stocks: pd.DataFrame, ticker: str, event_date: str, event_name: str = "") -> dict:
    frame = prices[prices["ticker"].eq(ticker)].copy() if prices is not None and not prices.empty else pd.DataFrame()
    if frame.empty:
        return _missing(ticker, event_name)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    event_ts = pd.to_datetime(event_date, errors="coerce")
    if pd.isna(event_ts):
        event_ts = frame["date"].max()
    frame = frame.dropna(subset=["date"]).sort_values("date")
    after = frame[frame["date"] >= event_ts]
    before = frame[frame["date"] < event_ts]
    if after.empty:
        after = frame.tail(1)
    event_row = after.iloc[0]
    prev_close = before.iloc[-1]["close"] if not before.empty else event_row.get("open")
    reaction_1d = _return(event_row.get("close"), prev_close)
    reaction_3d = _forward_return(after, event_row.get("close"), 3)
    reaction_5d = _forward_return(after, event_row.get("close"), 5)
    avg_value = frame[frame["date"] < event_row["date"]].tail(20)["trading_value"].mean()
    volume_spike = float(event_row.get("trading_value", 0) / avg_value) if avg_value and pd.notna(avg_value) else 0.0
    market_cap = _market_cap(stocks, ticker)
    market_cap_added = market_cap * (reaction_1d or 0) / 100 if market_cap else 0.0
    level = _pricing_level(reaction_1d, volume_spike)
    return {
        "date": _date_str(event_row["date"]),
        "ticker": ticker,
        "event_name": event_name,
        "price_reaction_1d": reaction_1d,
        "price_reaction_3d": reaction_3d,
        "price_reaction_5d": reaction_5d,
        "volume_spike": volume_spike,
        "market_cap_added": market_cap_added,
        "pricing_level": level,
        "interpretation": _interpretation(level, reaction_1d, volume_spike),
    }


def overheating_penalty(pricing_level: str) -> float:
    return {"LOW": 0, "MEDIUM": 3, "HIGH": 8, "EXTREME": 15}.get(pricing_level, 0)


def _pricing_level(reaction_1d: float, volume_spike: float) -> str:
    reaction = reaction_1d or 0
    abs_reaction = abs(reaction)
    if abs_reaction >= 15 or volume_spike >= 10:
        return "EXTREME"
    if abs_reaction >= 10 or volume_spike >= 5:
        return "HIGH"
    if abs_reaction >= 3 or volume_spike >= 2:
        return "MEDIUM"
    return "LOW"


def _interpretation(level: str, reaction_1d: float, volume_spike: float) -> str:
    if level in {"HIGH", "EXTREME"}:
        if reaction_1d is not None and reaction_1d < 0:
            return f"악재에 주가가 {reaction_1d:.1f}% 반응했고 거래대금 {volume_spike:.1f}배가 확인됩니다. 단기 충격은 크지만, 실적/수주/성장성 훼손 정도가 주가 하락보다 작은지 검증해야 합니다."
        return f"뉴스 자체가 긍정적이어도 당일 {reaction_1d:.1f}% 반응과 거래대금 {volume_spike:.1f}배가 확인되어 단기 기대감 선반영 가능성이 큽니다."
    if level == "MEDIUM":
        return f"주가 반응 {reaction_1d:.1f}%, 거래대금 {volume_spike:.1f}배로 일부 반영 상태입니다. 후속 공시와 실적 연결을 확인해야 합니다."
    return "주가 반응이 제한적입니다. 이벤트의 실적 연결 경로가 명확하면 2차 수혜 리서치 후보가 될 수 있습니다."


def _forward_return(after: pd.DataFrame, base_close: float, days: int):
    if after.empty or base_close in (None, 0) or pd.isna(base_close):
        return None
    idx = min(days - 1, len(after) - 1)
    return _return(after.iloc[idx].get("close"), base_close)


def _return(current, base):
    if base in (None, 0) or pd.isna(base) or current is None or pd.isna(current):
        return None
    return float((current / base - 1) * 100)


def _market_cap(stocks: pd.DataFrame, ticker: str) -> float:
    if stocks is None or stocks.empty:
        return 0.0
    matched = stocks[stocks["ticker"].eq(ticker)]
    return float(matched.iloc[0].get("market_cap") or 0) if not matched.empty else 0.0


def _date_str(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def _missing(ticker: str, event_name: str) -> dict:
    return {
        "date": "",
        "ticker": ticker,
        "event_name": event_name,
        "price_reaction_1d": None,
        "price_reaction_3d": None,
        "price_reaction_5d": None,
        "volume_spike": None,
        "market_cap_added": None,
        "pricing_level": "UNKNOWN",
        "interpretation": "가격 데이터가 부족해 주가 반영도를 계산할 수 없습니다.",
    }
