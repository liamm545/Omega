from __future__ import annotations

import pandas as pd

from event_impact.event_classifier import classify_event_type, relation_grade
from sector_intelligence.sector_registry import SECTOR_REGISTRY


def extract_events_from_news(news: pd.DataFrame, stocks: pd.DataFrame) -> list[dict]:
    if news is None or news.empty:
        return []
    stock_lookup = stocks.set_index("ticker").to_dict("index") if stocks is not None and not stocks.empty else {}
    events = []
    for _, row in news.sort_values("date", ascending=False).head(80).iterrows():
        text = f"{row.get('title', '')} {row.get('summary', '')} {row.get('keywords', '')}"
        sectors = _related_sectors(text)
        event_type = classify_event_type(text)
        ticker = row.get("ticker")
        company = stock_lookup.get(ticker, {}).get("name") if ticker else None
        is_negative = event_type.startswith("NEGATIVE")
        direct = [] if is_negative else ([company] if company else [])
        negative_companies = [company] if is_negative and company else []
        events.append(
            {
                "date": row.get("date"),
                "event_name": row.get("title") or "뉴스 이벤트",
                "event_type": event_type,
                "related_companies": direct,
                "related_sectors": sectors,
                "direct_beneficiaries": direct,
                "second_order_beneficiaries": [],
                "negative_impact_companies": negative_companies,
                "impact_timeframe": _timeframe(event_type),
                "earnings_link_probability": _earnings_probability(event_type, bool(company)),
                "relation_grade": relation_grade(event_type, bool(company)),
                "sentiment": "NEGATIVE" if is_negative else "POSITIVE_OR_NEUTRAL",
                "source_urls": [row.get("url")] if row.get("url") else [],
                "raw_text": text,
                "ticker": ticker,
            }
        )
    return events


def _related_sectors(text: str) -> list[str]:
    normalized = (text or "").lower()
    sectors = []
    for sector, config in SECTOR_REGISTRY.items():
        if any(keyword.lower() in normalized for keyword in config.get("keywords", [])):
            sectors.append(sector)
    return sectors or ["missing"]


def _earnings_probability(event_type: str, has_company: bool) -> float:
    if event_type.startswith("NEGATIVE"):
        return 0.25 if has_company else 0.15
    base = {
        "SUPPLY_CONTRACT": 0.8,
        "CAPEX": 0.7,
        "EARNINGS_SURPRISE": 0.75,
        "GUIDANCE_CHANGE": 0.7,
        "MOU": 0.45,
        "CEO_MEETING": 0.35,
        "KEYNOTE_MENTION": 0.3,
        "POLICY": 0.45,
        "EXPORT_DATA": 0.55,
        "INDUSTRY_DATA": 0.5,
    }.get(event_type, 0.35)
    return min(base + (0.1 if has_company else 0), 1.0)


def _timeframe(event_type: str) -> str:
    if event_type.startswith("NEGATIVE"):
        return "short/mid"
    if event_type in {"SUPPLY_CONTRACT", "EARNINGS_SURPRISE", "GUIDANCE_CHANGE"}:
        return "short/mid"
    if event_type in {"CAPEX", "POLICY", "EXPORT_DATA", "INDUSTRY_DATA"}:
        return "mid/long"
    return "short"
