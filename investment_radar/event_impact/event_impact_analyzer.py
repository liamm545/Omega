from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from event_impact.event_extractor import extract_events_from_news
from event_impact.market_pricing_analyzer import analyze_market_pricing
from event_impact.second_order_thinking import build_second_order_thesis


def analyze_event_impacts(tables: dict) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    news = tables.get("news", pd.DataFrame())
    stocks = tables.get("stocks", pd.DataFrame())
    prices = tables.get("daily_prices", pd.DataFrame())
    extracted = extract_events_from_news(news, stocks)
    impact_rows = []
    pricing_rows = []
    second_order = []
    for event in extracted[:30]:
        second = build_second_order_thesis(event, stocks)
        second_order.append(second)
        ticker = event.get("ticker")
        pricing = analyze_market_pricing(prices, stocks, ticker, event.get("date"), event.get("event_name")) if ticker else {}
        if pricing:
            pricing_rows.append(pricing)
        pricing_level = pricing.get("pricing_level", "UNKNOWN") if pricing else "UNKNOWN"
        implication = _implication(event, pricing_level)
        impact_rows.append(
            {
                "date": event.get("date"),
                "event_name": event.get("event_name"),
                "event_type": event.get("event_type"),
                "related_sectors_json": _json(event.get("related_sectors")),
                "related_companies_json": _json(event.get("related_companies")),
                "direct_beneficiaries_json": _json(event.get("direct_beneficiaries")),
                "second_order_beneficiaries_json": _json(second.get("candidate_sectors")),
                "impact_timeframe": event.get("impact_timeframe"),
                "earnings_link_probability": event.get("earnings_link_probability"),
                "market_pricing_level": pricing_level,
                "investment_implication": implication,
                "key_questions_json": _json(_key_questions(event, pricing_level)),
                "risk_factors_json": _json(_risk_factors(event, pricing_level)),
                "source_urls_json": _json(event.get("source_urls")),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return pd.DataFrame(impact_rows), pd.DataFrame(pricing_rows), second_order


def _implication(event: dict, pricing_level: str) -> str:
    if pricing_level in {"HIGH", "EXTREME"}:
        return "호재는 확인되지만 단기 가격 반영도가 높습니다. 추격보다 후속 계약/매출/CAPEX 확인과 2차 수혜 후보 검토가 필요합니다."
    if event.get("earnings_link_probability", 0) >= 0.6:
        return "실적 연결 가능성이 상대적으로 높은 리서치 후보입니다. 공식 공시와 수주/투자 규모를 확인해야 합니다."
    return "테마성 또는 초기 이벤트입니다. 출처 신뢰도와 실적 연결 경로 검증이 필요합니다."


def _key_questions(event: dict, pricing_level: str) -> list[str]:
    return [
        "공식 공시, 계약, MOU, CAPEX 중 어느 단계까지 확인되었는가?",
        "매출 또는 이익으로 연결될 시점과 규모가 있는가?",
        f"현재 주가 반영도는 {pricing_level}인데 후속 보도가 남아 있는가?",
    ]


def _risk_factors(event: dict, pricing_level: str) -> list[str]:
    risks = ["뉴스 출처 불확실성", "실적 연결 지연"]
    if pricing_level in {"HIGH", "EXTREME"}:
        risks.append("단기 과열 및 기대감 선반영")
    if event.get("relation_grade") == "SPECULATIVE":
        risks.append("단순 테마성 연결")
    return risks


def _json(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)
