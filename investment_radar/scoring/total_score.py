from functools import reduce

import pandas as pd

from scoring.common import grade_from_score
from scoring.event_score import calculate_event_score
from scoring.improvement_score import calculate_improvement_score
from scoring.momentum_score import calculate_momentum_score
from scoring.quality_score import calculate_quality_score
from scoring.risk_penalty import calculate_risk_penalty
from scoring.sector_score import calculate_sector_score
from scoring.valuation_score import calculate_valuation_score
from scoring.value_trap_filter import calculate_value_trap_flags
from industry_intelligence.cycle_detector import detect_industry_cycles
from industry_intelligence.industry_registry import industry_for_sector


def calculate_all_scores(tables: dict) -> pd.DataFrame:
    stocks = tables["stocks"]
    prices = tables["daily_prices"]
    financials = tables["financials"]
    valuation = tables["valuation_features"]
    news = tables["news"]
    events = tables["events"]
    event_map = tables["event_stock_map"]
    industry_kpis = tables.get("industry_kpis", pd.DataFrame())

    valuation_score = calculate_valuation_score(stocks, valuation, financials)
    quality_score = calculate_quality_score(financials)
    improvement_score = calculate_improvement_score(financials)
    momentum_score = calculate_momentum_score(prices)
    sector_score = calculate_sector_score(stocks, improvement_score, momentum_score, news)
    event_score = calculate_event_score(events, event_map)
    risk_penalty = calculate_risk_penalty(financials, prices, event_map)
    value_traps = calculate_value_trap_flags(financials, prices)

    frames = [
        stocks[["ticker", "name", "sector", "industry", "market_cap"]],
        valuation_score,
        quality_score,
        improvement_score,
        momentum_score,
        sector_score,
        event_score,
        risk_penalty,
        value_traps,
    ]
    score = reduce(lambda left, right: left.merge(right, on="ticker", how="left"), frames).fillna(0)
    score["industry_group"] = score["sector"].map(industry_for_sector)
    industry_cycles = detect_industry_cycles(industry_kpis)
    if not industry_cycles.empty:
        cycle_lookup = industry_cycles.set_index("industry")[["cycle_phase", "cycle_score"]]
        score = score.join(cycle_lookup, on="industry_group")
    else:
        score["cycle_phase"] = "missing"
        score["cycle_score"] = 0
    score["industry_cycle_adjustment"] = score["cycle_phase"].map(_cycle_adjustment).fillna(0)
    score["base_score"] = (
        0.20 * score["valuation_score"]
        + 0.15 * score["quality_score"]
        + 0.15 * score["improvement_score"]
        + 0.15 * score["momentum_score"]
        + 0.15 * score["sector_score"]
        + 0.20 * score["event_score"]
        - score["risk_penalty"]
        - score["risk_score"] * 0.35
    )
    score["total_score"] = (score["base_score"] + score["industry_cycle_adjustment"]).clip(0, 100)
    score["recommendation_reason"] = score.apply(_recommendation_reason, axis=1)
    score["grade"] = score["total_score"].apply(grade_from_score)
    return score.sort_values("total_score", ascending=False)


def _cycle_adjustment(phase: str) -> int:
    return {
        "초기 회복": 4,
        "성장": 8,
        "과열": 1,
        "정점": -5,
        "침체": -10,
    }.get(phase, 0)


def _recommendation_reason(row: pd.Series) -> str:
    reasons = []
    if row.get("cycle_phase") in ("초기 회복", "성장"):
        reasons.append(f"{row.get('industry_group')} {row.get('cycle_phase')}")
    if row.get("valuation_score", 0) >= 70:
        reasons.append("저평가 점수 우수")
    if row.get("improvement_score", 0) >= 60:
        reasons.append("실적 개선 신호")
    if row.get("event_score", 0) >= 50:
        reasons.append("이벤트 관련성 높음")
    if row.get("risk_flags"):
        reasons.append(f"리스크: {row.get('risk_flags')}")
    return " | ".join(reasons) if reasons else "추가 확인 필요"
