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
                "negative_impact_companies_json": _json(event.get("negative_impact_companies")),
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
    impacts = pd.DataFrame(impact_rows)
    if not impacts.empty:
        impacts = impacts.drop_duplicates(subset=["date", "event_name", "event_type"], keep="first")
    pricing = pd.DataFrame(pricing_rows)
    if not pricing.empty:
        pricing = pricing.drop_duplicates(subset=["ticker", "event_name"], keep="first")
    second_order = _dedupe_second_order(second_order)
    return impacts, pricing, second_order


def _implication(event: dict, pricing_level: str) -> str:
    if event.get("relation_grade") == "NEGATIVE":
        if pricing_level in {"HIGH", "EXTREME"}:
            return "악재성 이벤트입니다. 단기 주가 충격이 큰 만큼 사고/규제 비용, 수주잔고 훼손, 영업정지 가능성을 확인하고, 장기 성장성 대비 하락이 과도한지 별도로 검증해야 합니다."
        return "악재성 이벤트입니다. 직접 수혜가 아니라 리스크 이벤트로 분류하며, 실적 훼손 범위와 주가 반영도를 우선 확인해야 합니다."
    if pricing_level in {"HIGH", "EXTREME"}:
        return "호재는 확인되지만 단기 가격 반영도가 높습니다. 추격보다 후속 계약/매출/CAPEX 확인과 2차 수혜 후보 검토가 필요합니다."
    if event.get("earnings_link_probability", 0) >= 0.6:
        return "실적 연결 가능성이 상대적으로 높은 리서치 후보입니다. 공식 공시와 수주/투자 규모를 확인해야 합니다."
    return "테마성 또는 초기 이벤트입니다. 출처 신뢰도와 실적 연결 경로 검증이 필요합니다."


def _key_questions(event: dict, pricing_level: str) -> list[str]:
    if event.get("relation_grade") == "NEGATIVE":
        return [
            "사고/규제/책임 이슈가 일회성 비용인지 구조적 리스크인지 구분했는가?",
            "수주잔고, 납품 일정, 정부 제재 가능성에 실제 변화가 있는가?",
            f"주가 반영도는 {pricing_level}인데 하락 폭이 실적 훼손 가능성보다 과도한가?",
        ]
    return [
        "공식 공시, 계약, MOU, CAPEX 중 어느 단계까지 확인되었는가?",
        "매출 또는 이익으로 연결될 시점과 규모가 있는가?",
        f"현재 주가 반영도는 {pricing_level}인데 후속 보도가 남아 있는가?",
    ]


def _risk_factors(event: dict, pricing_level: str) -> list[str]:
    if event.get("relation_grade") == "NEGATIVE":
        risks = ["악재성 뉴스", "평판/정책 리스크", "일회성 비용 또는 제재 가능성"]
        if pricing_level in {"HIGH", "EXTREME"}:
            risks.append("단기 급락과 변동성 확대")
        return risks
    risks = ["뉴스 출처 불확실성", "실적 연결 지연"]
    if pricing_level in {"HIGH", "EXTREME"}:
        risks.append("단기 과열 및 기대감 선반영")
    if event.get("relation_grade") == "SPECULATIVE":
        risks.append("단순 테마성 연결")
    return risks


def _json(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _dedupe_second_order(items: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for item in items:
        key = item.get("event")
        if key in seen:
            continue
        seen.add(key)
        stocks = item.get("candidate_stocks", [])
        unique = {}
        for stock in stocks:
            unique[stock.get("ticker") or stock.get("name")] = stock
        item["candidate_stocks"] = list(unique.values())
        if item.get("second_order") or item.get("candidate_stocks") or item.get("third_order"):
            output.append(item)
    return output
