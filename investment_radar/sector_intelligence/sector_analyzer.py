from __future__ import annotations

import json
from datetime import date, datetime

import pandas as pd

from event_impact.event_impact_analyzer import analyze_event_impacts
from industry_kpi.kpi_signal import latest_kpi_status, sector_kpi_signal_score
from sector_intelligence.sector_cycle_detector import confidence_from_inputs, detect_sector_cycle
from sector_intelligence.sector_registry import SECTOR_REGISTRY, all_sector_names, sector_for_stock_sector
from sector_intelligence.sector_score import calculate_sector_market_scores


def build_sector_analysis(tables: dict, scores: pd.DataFrame) -> pd.DataFrame:
    stocks = tables.get("stocks", pd.DataFrame())
    news = tables.get("news", pd.DataFrame())
    kpis = tables.get("industry_kpis", pd.DataFrame())
    working_scores = scores.copy() if scores is not None and not scores.empty else pd.DataFrame()
    if not working_scores.empty and "intelligence_sector" not in working_scores.columns:
        working_scores["intelligence_sector"] = working_scores["sector"].map(sector_for_stock_sector)
    event_impacts, _, _ = analyze_event_impacts(tables)
    rows = []
    for sector in all_sector_names():
        config = SECTOR_REGISTRY[sector]
        kpi_score, kpi_pos, kpi_neg = sector_kpi_signal_score(kpis, sector)
        market = calculate_sector_market_scores(stocks, working_scores, sector)
        sector_news = _sector_news(news, config)
        sector_events = _sector_events(event_impacts, sector)
        news_score = min(len(sector_news) * 8, 100)
        event_score = min(len(sector_events) * 14 + market["event_score"] * 0.4, 100)
        stage, composite, pos, neg = detect_sector_cycle(kpi_score, market["momentum_score"], news_score, event_score, market["overheating"])
        confidence = confidence_from_inputs(len([item for item in latest_kpi_status(kpis, sector) if item.get("status") != "missing"]), len(sector_news), market["stock_count"])
        positive = (kpi_pos + pos + _news_titles(sector_news, 3))[:8]
        negative = (kpi_neg + neg)[:8]
        key_kpis = latest_kpi_status(kpis, sector)
        rows.append(
            {
                "date": date.today().isoformat(),
                "sector": sector,
                "cycle_stage": stage,
                "confidence": confidence,
                "sector_score": round(composite, 1),
                "positive_signals_json": _json(positive),
                "negative_signals_json": _json(negative),
                "key_kpis_json": _json(key_kpis),
                "beneficiary_groups_json": _json(config.get("beneficiary_groups", [])),
                "risk_factors_json": _json(config.get("risks", []) + negative),
                "watch_points_json": _json(config.get("watch_points", [])),
                "summary": _summary(sector, stage, positive, negative),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return pd.DataFrame(rows).sort_values(["sector_score", "confidence"], ascending=False)


def _sector_news(news: pd.DataFrame, config: dict) -> pd.DataFrame:
    if news is None or news.empty:
        return pd.DataFrame()
    pattern = "|".join([keyword for keyword in config.get("keywords", []) if keyword])
    if not pattern:
        return pd.DataFrame()
    text = news[["title", "summary", "keywords"]].fillna("").agg(" ".join, axis=1)
    return news[text.str.contains(pattern, case=False, regex=True, na=False)].sort_values("date", ascending=False)


def _sector_events(event_impacts: pd.DataFrame, sector: str) -> pd.DataFrame:
    if event_impacts is None or event_impacts.empty:
        return pd.DataFrame()
    return event_impacts[event_impacts["related_sectors_json"].fillna("").str.contains(sector, regex=False)]


def _news_titles(news: pd.DataFrame, limit: int) -> list[str]:
    if news.empty:
        return []
    return [f"뉴스: {title}" for title in news["title"].dropna().head(limit).tolist()]


def _summary(sector: str, stage: str, positive: list[str], negative: list[str]) -> str:
    if stage == "UNKNOWN":
        return f"{sector}는 현재 KPI/가격/뉴스 근거가 부족해 국면 판단을 보류합니다."
    sentence = f"{sector}는 현재 {stage} 국면으로 분류됩니다."
    if positive:
        sentence += f" 긍정 근거는 {positive[0]}입니다."
    if negative:
        sentence += f" 다만 {negative[0]}를 확인해야 합니다."
    return sentence


def _json(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)
