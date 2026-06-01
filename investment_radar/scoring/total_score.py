from functools import reduce

import pandas as pd

from event_impact.event_impact_analyzer import analyze_event_impacts
from event_impact.market_pricing_analyzer import overheating_penalty
from scoring.common import grade_from_score
from scoring.event_score import calculate_event_score
from scoring.improvement_score import calculate_improvement_score
from scoring.momentum_score import calculate_momentum_score
from scoring.quality_score import calculate_quality_score
from scoring.risk_penalty import calculate_risk_penalty
from scoring.sector_score import calculate_sector_score
from scoring.valuation_score import calculate_valuation_score
from scoring.value_trap_filter import calculate_value_trap_flags
from sector_intelligence.sector_analyzer import build_sector_analysis
from sector_intelligence.sector_cycle_detector import cycle_adjustment
from sector_intelligence.sector_registry import sector_for_stock_sector


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
    score = reduce(lambda left, right: left.merge(right, on="ticker", how="left"), frames)
    score = _fill_score_defaults(score)
    score["intelligence_sector"] = score["sector"].map(sector_for_stock_sector)
    latest_prices = prices.sort_values("date").groupby("ticker").tail(1) if not prices.empty else pd.DataFrame()
    if not latest_prices.empty:
        score = score.merge(latest_prices[["ticker", "return_1d", "return_1m", "return_3m"]], on="ticker", how="left")
    for column in ["return_1d", "return_1m", "return_3m"]:
        if column not in score.columns:
            score[column] = 0

    sector_analysis = build_sector_analysis(tables, score)
    if not sector_analysis.empty:
        sector_lookup = sector_analysis.set_index("sector")[["cycle_stage", "sector_score"]].rename(columns={"sector_score": "sector_cycle_score"})
        score = score.join(sector_lookup, on="intelligence_sector")
    else:
        score["cycle_stage"] = "UNKNOWN"
        score["sector_cycle_score"] = 0
    score["cycle_stage"] = score["cycle_stage"].fillna("UNKNOWN")
    score["sector_cycle_score"] = score["sector_cycle_score"].fillna(score["cycle_stage"].map(cycle_adjustment).fillna(40)).clip(0, 100)

    event_impacts, market_pricing, second_order = analyze_event_impacts(tables)
    score["event_impact_score"] = score["event_score"].fillna(0)
    if not event_impacts.empty:
        event_bonus = _event_impact_by_ticker(event_impacts, news)
        if not event_bonus.empty:
            score = score.merge(event_bonus, on="ticker", how="left")
            score["event_impact_score"] = score[["event_impact_score", "event_impact_bonus"]].max(axis=1).fillna(0)
            score = score.drop(columns=["event_impact_bonus"])
    score["second_order_score"] = score.apply(lambda row: _second_order_score(row, second_order), axis=1)
    if not market_pricing.empty:
        penalties = market_pricing.assign(overheating_penalty=lambda frame: frame["pricing_level"].apply(overheating_penalty)).groupby("ticker", as_index=False)["overheating_penalty"].max()
        score = score.merge(penalties, on="ticker", how="left")
    else:
        score["overheating_penalty"] = 0
    score["overheating_penalty"] = score["overheating_penalty"].fillna(0)

    score["base_score"] = (
        0.20 * score["valuation_score"]
        + 0.15 * score["quality_score"]
        + 0.15 * score["improvement_score"]
        + 0.10 * score["momentum_score"]
        + 0.20 * score["sector_cycle_score"]
        + 0.10 * score["event_impact_score"]
        + 0.10 * score["second_order_score"]
        - score["risk_penalty"]
        - score["risk_score"] * 0.35
        - score["overheating_penalty"]
    )
    score["total_score"] = score["base_score"].clip(0, 100)
    score["recommendation_reason"] = score.apply(_recommendation_reason, axis=1)
    score["grade"] = score["total_score"].apply(grade_from_score)
    return score.sort_values("total_score", ascending=False)


def _recommendation_reason(row: pd.Series) -> str:
    reasons = []
    if row.get("cycle_stage") in ("RECOVERY", "EXPANSION"):
        reasons.append(f"{row.get('intelligence_sector')} {row.get('cycle_stage')}")
    if row.get("cycle_stage") in ("OVERHEATED", "PEAKING"):
        reasons.append("섹터 과열/정점 가능성 검증 필요")
    if row.get("valuation_score", 0) >= 70:
        reasons.append("저평가 점수 우수")
    if row.get("improvement_score", 0) >= 60:
        reasons.append("실적 개선 신호")
    if row.get("event_score", 0) >= 50:
        reasons.append("이벤트 관련성 높음")
    if row.get("second_order_score", 0) >= 50:
        reasons.append("2차 수혜 리서치 후보")
    if row.get("overheating_penalty", 0) >= 8:
        reasons.append("단기 과열 경고")
    if row.get("risk_flags"):
        reasons.append(f"리스크: {row.get('risk_flags')}")
    return " | ".join(reasons) if reasons else "추가 확인 필요"


def _fill_score_defaults(score: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "market_cap",
        "valuation_score",
        "quality_score",
        "improvement_score",
        "momentum_score",
        "sector_score",
        "event_score",
        "risk_penalty",
        "risk_score",
    ]
    for column in numeric_columns:
        if column in score.columns:
            score[column] = pd.to_numeric(score[column], errors="coerce").fillna(0)
    for column in ["sector", "industry", "risk_flags"]:
        if column in score.columns:
            score[column] = score[column].fillna("")
    return score


def _event_impact_by_ticker(event_impacts: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    if news.empty:
        return pd.DataFrame(columns=["ticker", "event_impact_bonus"])
    rows = []
    for _, impact in event_impacts.iterrows():
        title = impact.get("event_name")
        matched = news[news["title"].eq(title)] if "title" in news.columns else pd.DataFrame()
        for ticker in matched.get("ticker", pd.Series(dtype=str)).dropna().unique():
            base = float(impact.get("earnings_link_probability") or 0) * 70
            pricing = impact.get("market_pricing_level")
            discount = {"HIGH": 8, "EXTREME": 15}.get(pricing, 0)
            rows.append({"ticker": ticker, "event_impact_bonus": max(base - discount, 0)})
    return pd.DataFrame(rows).groupby("ticker", as_index=False)["event_impact_bonus"].max() if rows else pd.DataFrame(columns=["ticker", "event_impact_bonus"])


def _second_order_score(row: pd.Series, second_order: list[dict]) -> float:
    text = f"{row.get('sector', '')} {row.get('industry', '')} {row.get('name', '')} {row.get('intelligence_sector', '')}".lower()
    score = 0
    for thesis in second_order:
        candidates = " ".join(thesis.get("candidate_sectors", [])).lower()
        if any(token and token in text for token in candidates.split()):
            score = max(score, 65)
        for stock in thesis.get("candidate_stocks", []):
            if stock.get("ticker") == row.get("ticker"):
                score = max(score, 80)
    if row.get("overheating_penalty", 0) >= 8:
        score = max(score - 20, 0)
    return float(score)
