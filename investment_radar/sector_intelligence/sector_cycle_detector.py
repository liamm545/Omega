from __future__ import annotations

import pandas as pd


def detect_sector_cycle(kpi_score: float, momentum_score: float, news_score: float, event_score: float, overheating: float) -> tuple[str, float, list[str], list[str]]:
    composite = 0.40 * kpi_score + 0.25 * momentum_score + 0.20 * news_score + 0.15 * event_score
    positives = []
    negatives = []
    if kpi_score >= 65:
        positives.append("핵심 KPI 개선")
    elif kpi_score <= 35 and kpi_score > 0:
        negatives.append("핵심 KPI 둔화")
    if momentum_score >= 60:
        positives.append("섹터 가격 모멘텀 양호")
    elif momentum_score <= 35:
        negatives.append("섹터 가격 모멘텀 약함")
    if news_score >= 60:
        positives.append("뉴스/공시 빈도 증가")
    if event_score >= 60:
        positives.append("이벤트 실적 연결 가능성 존재")
    if overheating >= 10:
        negatives.append("단기 과열 신호")

    if kpi_score == 0 and news_score == 0 and event_score < 20:
        return "UNKNOWN", composite, positives, ["핵심 KPI/뉴스 근거 부족"]
    if composite == 0:
        return "UNKNOWN", 0.0, positives, ["데이터 부족"]
    if overheating >= 12 and composite >= 70:
        return "OVERHEATED", composite, positives, negatives
    if composite >= 75:
        return "EXPANSION", composite, positives, negatives
    if composite >= 60:
        return "RECOVERY", composite, positives, negatives
    if composite >= 48:
        return "PEAKING" if overheating >= 8 else "SLOWDOWN", composite, positives, negatives
    if composite >= 35:
        return "SLOWDOWN", composite, positives, negatives
    return "CONTRACTION", composite, positives, negatives


def cycle_adjustment(stage: str) -> float:
    return {
        "RECOVERY": 80,
        "EXPANSION": 90,
        "OVERHEATED": 58,
        "PEAKING": 45,
        "SLOWDOWN": 30,
        "CONTRACTION": 15,
        "UNKNOWN": 40,
    }.get(stage, 40)


def confidence_from_inputs(kpi_count: int, news_count: int, stock_count: int) -> float:
    raw = 0.25 + min(kpi_count, 4) * 0.12 + min(news_count, 10) * 0.025 + min(stock_count, 5) * 0.04
    return round(min(raw, 0.9), 2)
