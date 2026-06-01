from __future__ import annotations

import json
from datetime import date

import pandas as pd

from event_impact.event_impact_analyzer import analyze_event_impacts
from llm.daily_briefing_prompt import DAILY_BRIEFING_SYSTEM_PROMPT
from sector_intelligence.sector_analyzer import build_sector_analysis
from utils.env import get_env


def generate_deep_daily_briefing(tables: dict, scores: pd.DataFrame) -> dict:
    context = build_deep_research_context(tables, scores)
    if get_env("OPENAI_API_KEY"):
        generated = _try_openai(context)
        if generated:
            return _validate(generated, context)
    return _fallback(context)


def build_deep_research_context(tables: dict, scores: pd.DataFrame) -> dict:
    sector_analysis = build_sector_analysis(tables, scores)
    event_impacts, market_pricing, second_order = analyze_event_impacts(tables)
    macro = tables.get("macro_indicators", pd.DataFrame())
    kpis = tables.get("industry_kpis", pd.DataFrame())
    news = tables.get("news", pd.DataFrame())
    filings = tables.get("filings", pd.DataFrame())
    return {
        "date": date.today().isoformat(),
        "market_snapshot": _records(_latest(macro, ["indicator"]), ["date", "indicator", "name", "value", "unit", "change_1d", "change_1m", "source"], 30),
        "sector_kpis": _records(kpis.sort_values("date", ascending=False) if not kpis.empty and "date" in kpis.columns else kpis, list(kpis.columns) if not kpis.empty else [], 60),
        "sector_analysis": _records(sector_analysis, list(sector_analysis.columns), 20),
        "news_events": _records(event_impacts, list(event_impacts.columns), 30),
        "filings": _records(filings.sort_values("rcept_dt", ascending=False) if not filings.empty and "rcept_dt" in filings.columns else filings, list(filings.columns) if not filings.empty else [], 20),
        "stock_scores": _records(scores, ["ticker", "name", "sector", "intelligence_sector", "total_score", "grade", "valuation_score", "quality_score", "improvement_score", "momentum_score", "sector_cycle_score", "event_impact_score", "second_order_score", "overheating_penalty", "recommendation_reason"], 40),
        "price_reactions": _records(market_pricing, list(market_pricing.columns), 30),
        "second_order": second_order[:20],
        "recent_news": _records(news.sort_values("date", ascending=False) if not news.empty and "date" in news.columns else news, ["date", "ticker", "title", "source", "url", "summary"], 30),
    }


def _try_openai(context: dict) -> dict:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=get_env("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=get_env("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.15,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": DAILY_BRIEFING_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {}


def _validate(payload: dict, context: dict) -> dict:
    fallback = _fallback(context)
    keys = fallback.keys()
    return {key: payload.get(key, fallback[key]) for key in keys}


def _fallback(context: dict) -> dict:
    sectors = sorted(context.get("sector_analysis", []), key=lambda item: item.get("sector_score") or 0, reverse=True)
    events = context.get("news_events", [])
    pricing = context.get("price_reactions", [])
    hot = [item for item in pricing if item.get("pricing_level") in {"HIGH", "EXTREME"}]
    second_order = context.get("second_order", [])
    top_scores = context.get("stock_scores", [])
    return {
        "date": context.get("date", date.today().isoformat()),
        "market_summary": _market_summary(context),
        "top_sector_insights": sectors[:5],
        "major_events": events[:10],
        "stock_watchlist": top_scores[:20],
        "overheated_stocks": hot[:10],
        "second_order_opportunities": second_order[:10],
        "risk_alerts": _risk_alerts(sectors, hot),
        "today_key_questions": [
            "호재가 공식 계약, 공시, CAPEX, 매출 중 어디까지 연결되었는가?",
            "직접 수혜주의 주가 반영도가 HIGH/EXTREME인지 확인했는가?",
            "2차 수혜 후보는 실적 연결 경로와 수주 가능성이 명확한가?",
            "섹터 KPI가 3개월 이상 같은 방향으로 유지되는가?",
            "반대 시나리오가 발생하면 어떤 KPI가 먼저 꺾이는가?",
        ],
        "conclusion": "수집된 데이터 기준으로 섹터 사이클과 이벤트 반영도를 함께 봐야 합니다. 직접 수혜주가 과열이면 2차 수혜 리서치 후보와 후속 공시 확인이 우선입니다.",
    }


def _market_summary(context: dict) -> str:
    macro = context.get("market_snapshot", [])
    if not macro:
        return "매크로 지표가 missing입니다. 매크로 업데이트 후 판단 정확도가 올라갑니다."
    names = [f"{item.get('name') or item.get('indicator')} {_fmt(item.get('value'))}{item.get('unit') or ''}" for item in macro[:6]]
    return " / ".join(names)


def _risk_alerts(sectors: list[dict], hot: list[dict]) -> list[dict]:
    alerts = []
    for item in sectors:
        if item.get("cycle_stage") in {"OVERHEATED", "PEAKING", "SLOWDOWN", "CONTRACTION"}:
            alerts.append({"type": "sector", "target": item.get("sector"), "reason": item.get("summary")})
    for item in hot:
        alerts.append({"type": "stock", "target": item.get("ticker"), "reason": item.get("interpretation")})
    return alerts[:12]


def _latest(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame.sort_values("date").groupby(keys, as_index=False).tail(1)


def _records(frame: pd.DataFrame, columns: list[str], limit: int) -> list[dict]:
    if frame is None or frame.empty or not columns:
        return []
    usable = [column for column in columns if column in frame.columns]
    return frame[usable].head(limit).where(pd.notna(frame[usable]), None).to_dict("records")


def _fmt(value) -> str:
    value = pd.to_numeric(value, errors="coerce")
    return "missing" if pd.isna(value) else f"{value:g}"
